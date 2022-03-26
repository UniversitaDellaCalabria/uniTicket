# Generated by Django 3.2.7 on 2021-11-11 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uni_ticket", "0171_ticketcategorywsprotocollo_protocollo_send_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticketcategorywsprotocollo",
            name="protocollo_email",
            field=models.EmailField(
                blank=True,
                help_text="Se vuoto: amministrazione@pec.unical.it",
                max_length=255,
                null=True,
                verbose_name="E-mail a RPA",
            ),
        ),
    ]