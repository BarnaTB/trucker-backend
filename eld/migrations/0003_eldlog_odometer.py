# Generated by Django 4.2.20 on 2025-04-10 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eld', '0002_driver_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='eldlog',
            name='odometer',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
