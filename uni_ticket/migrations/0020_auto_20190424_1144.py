# Generated by Django 2.1.7 on 2019-04-24 09:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uni_ticket', '0019_task_priority'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tickethistory',
            options={'ordering': ['ticket', '-modified'], 'verbose_name': 'Cronologia Stati Ticket', 'verbose_name_plural': 'Cronologia Stati Ticket'},
        ),
        migrations.RemoveField(
            model_name='taskhistory',
            name='employee',
        ),
        migrations.AddField(
            model_name='taskhistory',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
