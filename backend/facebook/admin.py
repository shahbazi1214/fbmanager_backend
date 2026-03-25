from django.contrib import admin
from .models import FacebookAccount, FacebookPage, PageDailyStats, AccountActivity, ManagerAccountAssignment


@admin.register(ManagerAccountAssignment)
class ManagerAccountAssignmentAdmin(admin.ModelAdmin):
    list_display = ['manager', 'account', 'assigned_by', 'assigned_at']
    list_filter = ['manager', 'assigned_at']
    search_fields = ['manager__username', 'account__name']


@admin.register(FacebookAccount)
class FacebookAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'owner', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email']


@admin.register(FacebookPage)
class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ['page_name', 'account', 'status', 'followers_count', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['page_name', 'page_id']


@admin.register(PageDailyStats)
class PageDailyStatsAdmin(admin.ModelAdmin):
    list_display = ['page', 'date', 'followers_count', 'new_followers']
    list_filter = ['date']


@admin.register(AccountActivity)
class AccountActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'account', 'page', 'created_at']
    list_filter = ['action', 'created_at']
