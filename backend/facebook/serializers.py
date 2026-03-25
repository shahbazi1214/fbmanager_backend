from rest_framework import serializers
from .models import FacebookAccount, FacebookPage, PageDailyStats, AccountActivity, ManagerAccountAssignment


class PageDailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageDailyStats
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PageDailyStatsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageDailyStats
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class FacebookPageListSerializer(serializers.ModelSerializer):
    latest_stats = PageDailyStatsSerializer(read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = FacebookPage
        fields = [
            'id', 'account', 'account_name', 'page_name', 'page_id', 'page_url',
            'category', 'description', 'followers_count', 'likes_count',
            'total_posts', 'total_reels', 'total_videos', 'profile_picture_url',
            'cover_photo_url', 'status', 'monetization_enabled', 'verified',
            'notes', 'latest_stats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacebookPageDetailSerializer(serializers.ModelSerializer):
    daily_stats = PageDailyStatsSerializer(many=True, read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    stats_last_3_days = serializers.SerializerMethodField()

    class Meta:
        model = FacebookPage
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_stats_last_3_days(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now().date() - timedelta(days=3)
        stats = obj.daily_stats.filter(date__gte=cutoff).order_by('date')
        return PageDailyStatsSerializer(stats, many=True).data


class AccountActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    page_name = serializers.CharField(source='page.page_name', read_only=True)

    class Meta:
        model = AccountActivity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class FacebookAccountListSerializer(serializers.ModelSerializer):
    pages_count = serializers.IntegerField(read_only=True)
    active_pages_count = serializers.IntegerField(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    assigned_managers = serializers.SerializerMethodField()

    class Meta:
        model = FacebookAccount
        fields = [
            'id', 'owner', 'owner_name', 'name', 'email', 'profile_url',
            'profile_id', 'status', 'pages_count', 'active_pages_count',
            'last_login', 'created_at', 'updated_at', 'notes', 'assigned_managers'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_managers(self, obj):
        assignments = obj.assignments.select_related('manager').all()
        return [
            {'id': a.manager.id, 'username': a.manager.username, 'email': a.manager.email}
            for a in assignments
        ]


class FacebookAccountDetailSerializer(serializers.ModelSerializer):
    pages = FacebookPageListSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    pages_count = serializers.IntegerField(read_only=True)
    active_pages_count = serializers.IntegerField(read_only=True)
    recent_activities = serializers.SerializerMethodField()
    assigned_managers = serializers.SerializerMethodField()

    class Meta:
        model = FacebookAccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_recent_activities(self, obj):
        activities = obj.activities.all()[:10]
        return AccountActivitySerializer(activities, many=True).data

    def get_assigned_managers(self, obj):
        assignments = obj.assignments.select_related('manager').all()
        return [
            {'id': a.manager.id, 'username': a.manager.username, 'email': a.manager.email}
            for a in assignments
        ]


class FacebookAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookAccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
