# Generated by Django 3.0.3 on 2020-03-17 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0057_auto_20200317_1018'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ticket',
            old_name='taked_by',
            new_name='taken_by',
        ),
    ]
