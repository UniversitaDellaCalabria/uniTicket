# Generated by Django 3.2.12 on 2022-04-04 10:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [('chat', '0001_initial'), ('chat', '0002_auto_20200303_1416'), ('chat', '0003_chatmessagemodel_read_date'), ('chat', '0004_auto_20200303_1422'), ('chat', '0005_auto_20200305_1556'), ('chat', '0006_auto_20200305_1628'), ('chat', '0007_auto_20200305_1635'), ('chat', '0008_userchannel'), ('chat', '0009_userchannel_room'), ('chat', '0010_userchannel_last_seen'), ('chat', '0011_auto_20200402_0931'), ('chat', '0012_userchannel_status')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessageModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='body')),
                ('recipient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_user', to=settings.AUTH_USER_MODEL, verbose_name='recipient')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_user', to=settings.AUTH_USER_MODEL, verbose_name='user')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now)),
                ('room', models.CharField(blank=True, max_length=150, null=True)),
                ('read_date', models.DateTimeField(blank=True, editable=False, null=True)),
                ('broadcast', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'message',
                'verbose_name_plural': 'messages',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='UserChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(max_length=150)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
                ('room', models.CharField(blank=True, max_length=150, null=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('status', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Canale Utente',
                'verbose_name_plural': 'Canali Utenti',
                'ordering': ('-created',),
            },
        ),
    ]