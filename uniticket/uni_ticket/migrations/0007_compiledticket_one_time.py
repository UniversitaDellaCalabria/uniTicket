# Generated by Django 3.2.15 on 2023-02-03 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0006_alter_compiledticket_url_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='compiledticket',
            name='one_time',
            field=models.BooleanField(default=False),
        ),
    ]
