from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Facebook Accounts
    path('accounts/', views.FacebookAccountListView.as_view(), name='fb_accounts'),
    path('accounts/<int:pk>/', views.FacebookAccountDetailView.as_view(), name='fb_account_detail'),

    # Facebook Pages
    path('pages/', views.FacebookPageListView.as_view(), name='fb_pages'),
    path('pages/<int:pk>/', views.FacebookPageDetailView.as_view(), name='fb_page_detail'),

    # Daily Stats
    path('pages/<int:page_id>/stats/', views.PageDailyStatsListView.as_view(), name='page_stats'),
    path('stats/<int:pk>/', views.PageDailyStatsDetailView.as_view(), name='stat_detail'),
    path('pages/<int:page_id>/progress/', views.PageProgressView.as_view(), name='page_progress'),
]
