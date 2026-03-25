from django.db import models
from django.conf import settings
import base64
import json


class ManagerAccountAssignment(models.Model):
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_accounts',
    )
    account = models.ForeignKey(
        'FacebookAccount',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'manager_account_assignments'
        unique_together = ['manager', 'account']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.manager.username} -> {self.account.name}"


class FacebookAccount(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('checkpoint', 'Checkpoint'),
        ('disabled', 'Disabled'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fb_accounts'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=500)
    two_fa_code = models.CharField(max_length=100, blank=True, verbose_name='2FA Secret/Code')
    date_of_birth = models.DateField(null=True, blank=True)
    profile_url = models.URLField(blank=True)
    profile_id = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    recovery_email = models.EmailField(blank=True)
    proxy = models.CharField(max_length=200, blank=True, help_text='Proxy IP:PORT')
    user_agent = models.TextField(blank=True)
    cookies = models.TextField(blank=True, help_text='Account cookies JSON')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fb_accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def pages_count(self):
        return self.pages.count()

    @property
    def active_pages_count(self):
        return self.pages.filter(status='active').count()


class FacebookPage(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('restricted', 'Restricted'),
        ('unpublished', 'Unpublished'),
        ('banned', 'Banned'),
    ]
    CATEGORY_CHOICES = [
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('news', 'News & Media'),
        ('community', 'Community'),
        ('brand', 'Brand'),
        ('artist', 'Artist'),
        ('public_figure', 'Public Figure'),
        ('education', 'Education'),
        ('nonprofit', 'Non-Profit'),
        ('sports', 'Sports'),
        ('tech', 'Technology'),
        ('other', 'Other'),
    ]

    account = models.ForeignKey(
        FacebookAccount,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    page_name = models.CharField(max_length=255)
    page_id = models.CharField(max_length=100, blank=True)
    page_url = models.URLField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    total_posts = models.PositiveIntegerField(default=0)
    total_reels = models.PositiveIntegerField(default=0)
    total_videos = models.PositiveIntegerField(default=0)
    profile_picture_url = models.URLField(blank=True)
    cover_photo_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    monetization_enabled = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fb_pages'
        ordering = ['-followers_count']

    def __str__(self):
        return f"{self.page_name} ({self.account.name})"

    @property
    def latest_stats(self):
        return self.daily_stats.order_by('-date').first()


class PageDailyStats(models.Model):
    page = models.ForeignKey(
        FacebookPage,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField()
    followers_count = models.PositiveIntegerField(default=0)
    new_followers = models.IntegerField(default=0)
    lost_followers = models.IntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    post_reach = models.PositiveIntegerField(default=0)
    post_impressions = models.PositiveIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    new_posts = models.PositiveIntegerField(default=0)
    new_reels = models.PositiveIntegerField(default=0)
    new_videos = models.PositiveIntegerField(default=0)
    new_likes = models.IntegerField(default=0)
    total_reactions = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'page_daily_stats'
        ordering = ['-date']
        unique_together = ['page', 'date']

    def __str__(self):
        return f"{self.page.page_name} - {self.date}"


class AccountActivity(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('post_created', 'Post Created'),
        ('reel_created', 'Reel Created'),
        ('page_updated', 'Page Updated'),
        ('stats_updated', 'Stats Updated'),
        ('status_changed', 'Status Changed'),
        ('note_added', 'Note Added'),
    ]
    account = models.ForeignKey(
        FacebookAccount,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True, blank=True
    )
    page = models.ForeignKey(
        FacebookPage,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True, blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'account_activities'
        ordering = ['-created_at']
