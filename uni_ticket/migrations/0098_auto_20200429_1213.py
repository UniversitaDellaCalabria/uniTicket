# Generated by Django 3.0.5 on 2020-04-29 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uni_ticket', '0097_auto_20200428_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketcategoryinputlist',
            name='valore',
            field=models.TextField(blank=True, default='', help_text="Viene considerato solo se si sceglie 'Menu a tendina' oppure 'Serie di Opzioni'. (Es: valore1;valore2;valore3...)", max_length=10000, verbose_name='Lista di Valori'),
        ),
    ]
