# Generated by Django 3.2.15 on 2023-02-03 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0004_alter_ticketcategorywsprotocollo_protocollo_uo'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompiledTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_path', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
