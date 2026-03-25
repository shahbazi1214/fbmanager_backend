from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from datetime import timedelta, date
from .models import FacebookAccount, FacebookPage, PageDailyStats, AccountActivity, ManagerAccountAssignment
from .serializers import (
    FacebookAccountListSerializer, FacebookAccountDetailSerializer,
    FacebookAccountCreateSerializer, FacebookPageListSerializer,
    FacebookPageDetailSerializer, PageDailyStatsSerializer,
    PageDailyStatsCreateSerializer, AccountActivitySerializer,
)
from accounts.permissions import IsAdmin, IsAdminOrManager
from accounts.models import CustomUser


def get_accessible_accounts(user):
    """Return accounts the user can access based on role."""
    if user.role == 'admin':
        return FacebookAccount.objects.all()
    # Manager: only assigned accounts
    assigned_ids = ManagerAccountAssignment.objects.filter(
        manager=user
    ).values_list('account_id', flat=True)
    return FacebookAccount.objects.filter(id__in=assigned_ids)


def get_accessible_pages(user):
    """Return pages the user can access based on role."""
    if user.role == 'admin':
        return FacebookPage.objects.select_related('account').all()
    assigned_ids = ManagerAccountAssignment.objects.filter(
        manager=user
    ).values_list('account_id', flat=True)
    return FacebookPage.objects.select_related('account').filter(account_id__in=assigned_ids)


class FacebookAccountListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        qs = get_accessible_accounts(user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FacebookAccountCreateSerializer
        return FacebookAccountListSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'detail': 'Only admins can create accounts.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FacebookAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        AccountActivity.objects.create(
            account=account,
            user=request.user,
            action='status_changed',
            description=f'Account "{account.name}" created'
        )
        return Response(FacebookAccountDetailSerializer(account).data, status=status.HTTP_201_CREATED)


class FacebookAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        return get_accessible_accounts(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FacebookAccountCreateSerializer
        return FacebookAccountDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = FacebookAccountCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        AccountActivity.objects.create(
            account=account,
            user=request.user,
            action='status_changed',
            description=f'Account "{account.name}" updated'
        )
        return Response(FacebookAccountDetailSerializer(account).data)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'detail': 'Only admins can delete accounts.'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return Response({'detail': f'Account "{name}" deleted'}, status=status.HTTP_204_NO_CONTENT)


class FacebookPageListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        qs = get_accessible_pages(user)

        account_id = self.request.query_params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(page_name__icontains=search) | Q(page_id__icontains=search))

        return qs

    def get_serializer_class(self):
        return FacebookPageListSerializer

    def create(self, request, *args, **kwargs):
        serializer = FacebookPageListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check manager can only create pages on assigned accounts
        if request.user.role == 'manager':
            account_id = serializer.validated_data.get('account').id
            has_access = ManagerAccountAssignment.objects.filter(
                manager=request.user, account_id=account_id
            ).exists()
            if not has_access:
                return Response({'detail': 'You do not have access to this account.'}, status=status.HTTP_403_FORBIDDEN)

        page = serializer.save()
        AccountActivity.objects.create(
            account=page.account,
            page=page,
            user=request.user,
            action='page_updated',
            description=f'Page "{page.page_name}" added to account "{page.account.name}"'
        )
        return Response(FacebookPageDetailSerializer(page).data, status=status.HTTP_201_CREATED)


class FacebookPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        return get_accessible_pages(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FacebookPageListSerializer
        return FacebookPageDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = FacebookPageListSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        page = serializer.save()
        AccountActivity.objects.create(
            account=page.account,
            page=page,
            user=request.user,
            action='page_updated',
            description=f'Page "{page.page_name}" updated'
        )
        return Response(FacebookPageDetailSerializer(page).data)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'detail': 'Only admins can delete pages.'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageDailyStatsListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = PageDailyStatsSerializer

    def get_queryset(self):
        page_id = self.kwargs.get('page_id')
        qs = PageDailyStats.objects.filter(page_id=page_id)
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        cutoff = timezone.now().date() - timedelta(days=days)
        qs = qs.filter(date__gte=cutoff).order_by('date')
        return qs

    def create(self, request, *args, **kwargs):
        page_id = self.kwargs.get('page_id')

        # Check access for managers
        if request.user.role == 'manager':
            try:
                page = FacebookPage.objects.get(pk=page_id)
                has_access = ManagerAccountAssignment.objects.filter(
                    manager=request.user, account=page.account
                ).exists()
                if not has_access:
                    return Response({'detail': 'You do not have access to this page.'}, status=status.HTTP_403_FORBIDDEN)
            except FacebookPage.DoesNotExist:
                return Response({'detail': 'Page not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['page'] = page_id
        serializer = PageDailyStatsCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        stats = serializer.save()

        page = stats.page
        if stats.followers_count > 0:
            page.followers_count = stats.followers_count
            page.save(update_fields=['followers_count'])

        AccountActivity.objects.create(
            account=page.account,
            page=page,
            user=request.user,
            action='stats_updated',
            description=f'Daily stats updated for "{page.page_name}" on {stats.date}'
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PageDailyStatsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = PageDailyStatsSerializer
    queryset = PageDailyStats.objects.all()


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        accounts = get_accessible_accounts(user)
        pages = get_accessible_pages(user)

        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)

        recent_stats = PageDailyStats.objects.filter(
            page__in=pages,
            date__gte=last_7_days
        )

        account_statuses = dict(
            accounts.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        page_statuses = dict(
            pages.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        total_followers = pages.aggregate(total=Sum('followers_count'))['total'] or 0
        new_followers_7d = recent_stats.aggregate(total=Sum('new_followers'))['total'] or 0

        today_stats = recent_stats.filter(date=today)
        new_posts_today = today_stats.aggregate(total=Sum('new_posts'))['total'] or 0
        new_reels_today = today_stats.aggregate(total=Sum('new_reels'))['total'] or 0

        chart_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_stats = recent_stats.filter(date=d)
            chart_data.append({
                'date': str(d),
                'new_followers': day_stats.aggregate(total=Sum('new_followers'))['total'] or 0,
                'page_views': day_stats.aggregate(total=Sum('page_views'))['total'] or 0,
                'new_posts': day_stats.aggregate(total=Sum('new_posts'))['total'] or 0,
                'new_reels': day_stats.aggregate(total=Sum('new_reels'))['total'] or 0,
            })

        top_pages = pages.order_by('-followers_count')[:5]
        top_pages_data = FacebookPageListSerializer(top_pages, many=True).data

        activities = AccountActivity.objects.filter(
            Q(account__in=accounts) | Q(page__account__in=accounts)
        )[:15]
        activities_data = AccountActivitySerializer(activities, many=True).data

        # Admin-only: manager overview
        manager_stats = None
        if user.role == 'admin':
            managers = CustomUser.objects.filter(role='manager')
            manager_stats = []
            for mgr in managers:
                mgr_account_ids = ManagerAccountAssignment.objects.filter(
                    manager=mgr
                ).values_list('account_id', flat=True)
                mgr_accounts_qs = FacebookAccount.objects.filter(id__in=mgr_account_ids)
                mgr_pages_qs = FacebookPage.objects.filter(account_id__in=mgr_account_ids)
                mgr_followers = mgr_pages_qs.aggregate(total=Sum('followers_count'))['total'] or 0
                manager_stats.append({
                    'id': mgr.id,
                    'username': mgr.username,
                    'first_name': mgr.first_name,
                    'last_name': mgr.last_name,
                    'email': mgr.email,
                    'accounts_count': mgr_accounts_qs.count(),
                    'pages_count': mgr_pages_qs.count(),
                    'total_followers': mgr_followers,
                })

        response_data = {
            'summary': {
                'total_accounts': accounts.count(),
                'active_accounts': accounts.filter(status='active').count(),
                'total_pages': pages.count(),
                'active_pages': pages.filter(status='active').count(),
                'total_followers': total_followers,
                'new_followers_7d': new_followers_7d,
                'new_posts_today': new_posts_today,
                'new_reels_today': new_reels_today,
            },
            'account_statuses': account_statuses,
            'page_statuses': page_statuses,
            'chart_data': chart_data,
            'top_pages': top_pages_data,
            'recent_activities': activities_data,
        }

        if manager_stats is not None:
            response_data['manager_stats'] = manager_stats

        return Response(response_data)


class PageProgressView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request, page_id):
        try:
            page = FacebookPage.objects.get(pk=page_id)
        except FacebookPage.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check access for managers
        if request.user.role == 'manager':
            has_access = ManagerAccountAssignment.objects.filter(
                manager=request.user, account=page.account
            ).exists()
            if not has_access:
                return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        cutoff = today - timedelta(days=days)

        stats = PageDailyStats.objects.filter(
            page=page,
            date__gte=cutoff
        ).order_by('date')

        return Response({
            'page': FacebookPageListSerializer(page).data,
            'stats': PageDailyStatsSerializer(stats, many=True).data,
            'summary': {
                'total_new_followers': stats.aggregate(total=Sum('new_followers'))['total'] or 0,
                'total_page_views': stats.aggregate(total=Sum('page_views'))['total'] or 0,
                'total_new_posts': stats.aggregate(total=Sum('new_posts'))['total'] or 0,
                'total_new_reels': stats.aggregate(total=Sum('new_reels'))['total'] or 0,
                'avg_engagement': stats.aggregate(avg=Avg('engagement_rate'))['avg'] or 0,
            }
        })
