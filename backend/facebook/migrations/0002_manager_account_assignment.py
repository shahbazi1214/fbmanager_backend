from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facebook', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ManagerAccountAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('manager', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assigned_accounts',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('account', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='facebook.facebookaccount',
                )),
                ('assigned_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_assignments',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'manager_account_assignments',
                'ordering': ['-assigned_at'],
                'unique_together': {('manager', 'account')},
            },
        ),
    ]
