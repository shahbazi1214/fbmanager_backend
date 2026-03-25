from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role in ['admin', 'manager']
