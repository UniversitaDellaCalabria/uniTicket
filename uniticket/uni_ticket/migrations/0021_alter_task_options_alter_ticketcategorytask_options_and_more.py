# Generated by Django 4.2.9 on 2024-06-06 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0020_task_closing_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='ordering',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='ticketcategorytask',
            name='ordering',
            field=models.IntegerField(default=10),
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['ordering', 'created'], 'verbose_name': 'Task', 'verbose_name_plural': 'Task'},
        ),
        migrations.AlterModelOptions(
            name='ticketcategorytask',
            options={'ordering': ['ordering', 'created'], 'verbose_name': 'Task predefinito', 'verbose_name_plural': 'Task predefiniti'},
        ),
    ]
