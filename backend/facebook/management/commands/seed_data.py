from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from facebook.models import FacebookAccount, FacebookPage, PageDailyStats, AccountActivity, ManagerAccountAssignment
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial demo data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating users...')

        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@fbmanager.com', 'first_name': 'Admin', 'last_name': 'User',
            'role': 'admin', 'is_staff': True, 'is_superuser': True,
        })
        admin.set_password('admin123')
        admin.save()

        manager1, _ = User.objects.get_or_create(username='manager', defaults={
            'email': 'manager@fbmanager.com', 'first_name': 'John', 'last_name': 'Manager',
            'role': 'manager',
        })
        manager1.set_password('manager123')
        manager1.save()

        manager2, _ = User.objects.get_or_create(username='manager2', defaults={
            'email': 'manager2@fbmanager.com', 'first_name': 'Sarah', 'last_name': 'Manager',
            'role': 'manager',
        })
        manager2.set_password('manager123')
        manager2.save()

        self.stdout.write('Creating Facebook accounts...')

        acc1, _ = FacebookAccount.objects.get_or_create(email='john.smith@gmail.com', defaults={
            'owner': admin, 'name': 'John Smith', 'password': 'SecurePass@123',
            'two_fa_code': 'JBSWY3DPEHPK3PXP', 'profile_url': 'https://facebook.com/johnsmith',
            'status': 'active', 'notes': 'Primary personal account',
        })
        acc2, _ = FacebookAccount.objects.get_or_create(email='sarah.j@gmail.com', defaults={
            'owner': admin, 'name': 'Sarah Johnson', 'password': 'MyFbPass#456',
            'two_fa_code': 'MFZWY3DPHEZK3QXP', 'profile_url': 'https://facebook.com/sarahj',
            'status': 'active',
        })
        acc3, _ = FacebookAccount.objects.get_or_create(email='techbrand@company.com', defaults={
            'owner': admin, 'name': 'Tech Brand Corp', 'password': 'TechBrand@789',
            'profile_url': 'https://facebook.com/techbrand', 'status': 'active',
        })
        acc4, _ = FacebookAccount.objects.get_or_create(email='oldaccount@mail.com', defaults={
            'owner': admin, 'name': 'Old Account', 'password': 'OldPass@111',
            'status': 'suspended', 'notes': 'Suspended due to policy violation',
        })

        self.stdout.write('Assigning accounts to managers...')
        # Assign acc1 and acc2 to manager1
        for acc in [acc1, acc2]:
            ManagerAccountAssignment.objects.get_or_create(
                manager=manager1, account=acc,
                defaults={'assigned_by': admin}
            )
        # Assign acc3 to manager2
        ManagerAccountAssignment.objects.get_or_create(
            manager=manager2, account=acc3,
            defaults={'assigned_by': admin}
        )

        self.stdout.write('Creating Facebook pages...')

        pages_data = [
            {'account': acc1, 'page_name': 'Tech News Daily', 'page_id': '123456789',
             'page_url': 'https://facebook.com/technewsdaily', 'category': 'news',
             'followers_count': 45200, 'likes_count': 44800, 'total_posts': 342, 'total_reels': 89,
             'status': 'active', 'verified': True, 'monetization_enabled': True},
            {'account': acc1, 'page_name': 'Startup World', 'page_id': '987654321',
             'page_url': 'https://facebook.com/startupworld', 'category': 'business',
             'followers_count': 23100, 'likes_count': 22900, 'total_posts': 198, 'total_reels': 45,
             'status': 'active'},
            {'account': acc2, 'page_name': 'Cooking Paradise', 'page_id': '111222333',
             'page_url': 'https://facebook.com/cookingparadise', 'category': 'entertainment',
             'followers_count': 78500, 'likes_count': 77200, 'total_posts': 512, 'total_reels': 234,
             'status': 'active', 'monetization_enabled': True},
            {'account': acc2, 'page_name': 'Travel & Adventure', 'page_id': '222333444',
             'page_url': 'https://facebook.com/traveladventure', 'category': 'entertainment',
             'followers_count': 34700, 'likes_count': 34100, 'total_posts': 265, 'total_reels': 112,
             'status': 'active'},
            {'account': acc3, 'page_name': 'TechBrand Official', 'page_id': '444555666',
             'page_url': 'https://facebook.com/techbrandofficial', 'category': 'tech',
             'followers_count': 12300, 'likes_count': 12100, 'total_posts': 87, 'total_reels': 23,
             'status': 'active', 'verified': True},
            {'account': acc4, 'page_name': 'Old Memes Page', 'page_id': '777888999',
             'page_url': 'https://facebook.com/oldmemes', 'category': 'entertainment',
             'followers_count': 5600, 'likes_count': 5400, 'total_posts': 89, 'total_reels': 12,
             'status': 'restricted'},
        ]

        pages = []
        for data in pages_data:
            page, _ = FacebookPage.objects.get_or_create(page_id=data['page_id'], defaults=data)
            pages.append(page)

        self.stdout.write('Creating 14 days of daily stats...')
        today = timezone.now().date()
        for page in pages:
            base = page.followers_count
            for i in range(13, -1, -1):
                d = today - timedelta(days=i)
                PageDailyStats.objects.get_or_create(page=page, date=d, defaults={
                    'followers_count': max(0, base - i * random.randint(30, 200)),
                    'new_followers': random.randint(50, 800),
                    'lost_followers': random.randint(5, 60),
                    'page_views': random.randint(400, 8000),
                    'post_reach': random.randint(1000, 30000),
                    'post_impressions': random.randint(2000, 60000),
                    'engagement_rate': round(random.uniform(2.0, 9.5), 2),
                    'new_posts': random.randint(0, 5),
                    'new_reels': random.randint(0, 3),
                    'new_videos': random.randint(0, 2),
                    'new_likes': random.randint(20, 400),
                    'total_reactions': random.randint(100, 1500),
                    'comments_count': random.randint(20, 300),
                    'shares_count': random.randint(10, 150),
                    'clicks': random.randint(50, 800),
                })

        self.stdout.write('Creating activity logs...')
        AccountActivity.objects.get_or_create(
            account=acc1, user=admin, action='status_changed',
            defaults={'description': 'Account "John Smith" created'}
        )
        AccountActivity.objects.get_or_create(
            account=acc2, page=pages[2], user=manager1, action='page_updated',
            defaults={'description': 'Page "Cooking Paradise" stats updated'}
        )

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Seed data created!\n'
            '  admin / admin123  (sees everything)\n'
            '  manager / manager123  (assigned: John Smith, Sarah Johnson accounts)\n'
            '  manager2 / manager123  (assigned: Tech Brand Corp account)\n'
        ))
