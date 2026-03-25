from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'avatar')}),
    )
