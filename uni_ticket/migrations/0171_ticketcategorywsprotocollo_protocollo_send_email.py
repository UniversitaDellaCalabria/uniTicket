# Generated by Django 3.2.7 on 2021-11-11 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0170_alter_ticketcategory_footer_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketcategorywsprotocollo',
            name='protocollo_send_email',
            field=models.BooleanField(default=True, verbose_name='Invia e-mail'),
        ),
    ]