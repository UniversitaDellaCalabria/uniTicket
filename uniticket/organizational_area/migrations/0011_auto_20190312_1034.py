# Generated by Django 2.1.7 on 2019-03-12 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizational_area', '0010_auto_20190312_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationalstructureoffice',
            name='name',
            field=models.CharField(max_length=128),
        ),
    ]