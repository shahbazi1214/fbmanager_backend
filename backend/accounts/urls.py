from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('users/', views.UserListCreateView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    # Assignment endpoints used by frontend
    path('users/<int:pk>/assign-accounts/', views.UserAssignAccountsView.as_view(), name='user_assign_accounts'),
    path('users/<int:pk>/assigned-accounts/', views.UserAssignedAccountsView.as_view(), name='user_assigned_accounts'),
]
