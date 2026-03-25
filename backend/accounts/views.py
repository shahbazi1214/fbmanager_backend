from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer
)
from .permissions import IsAdmin


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'detail': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out successfully'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password updated successfully'})


class UserListCreateView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance).data)


class UserAssignAccountsView(APIView):
    """
    POST /api/auth/users/{id}/assign-accounts/
    Body: { account_ids: [1, 2, 3] }
    Replaces all assignments for this manager.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        from facebook.models import FacebookAccount, ManagerAccountAssignment

        try:
            manager = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if manager.role != 'manager':
            return Response({'detail': 'User must have the manager role.'}, status=status.HTTP_400_BAD_REQUEST)

        account_ids = request.data.get('account_ids', [])
        if not isinstance(account_ids, list):
            return Response({'detail': 'account_ids must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        # Replace all existing assignments
        ManagerAccountAssignment.objects.filter(manager=manager).delete()

        created = []
        for acc_id in account_ids:
            try:
                account = FacebookAccount.objects.get(pk=acc_id)
                assignment = ManagerAccountAssignment.objects.create(
                    manager=manager,
                    account=account,
                    assigned_by=request.user
                )
                created.append(assignment)
            except FacebookAccount.DoesNotExist:
                pass

        return Response({
            'detail': f'{len(created)} accounts assigned to {manager.username}.',
            'assigned_count': len(created),
        })


class UserAssignedAccountsView(APIView):
    """
    GET /api/auth/users/{id}/assigned-accounts/
    Returns list of accounts assigned to a manager.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        from facebook.models import ManagerAccountAssignment
        from facebook.serializers import FacebookAccountListSerializer

        try:
            manager = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        assignments = ManagerAccountAssignment.objects.filter(
            manager=manager
        ).select_related('account')

        accounts = [a.account for a in assignments]
        from facebook.serializers import FacebookAccountListSerializer
        data = FacebookAccountListSerializer(accounts, many=True).data
        return Response(data)
