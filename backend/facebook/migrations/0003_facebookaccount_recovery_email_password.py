from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facebook', '0002_manager_account_assignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookaccount',
            name='recovery_email_password',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
