# Generated by Django 2.0.2 on 2019-11-01 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0025_auto_20191101_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='grade',
            field=models.FloatField(default=0.0),
        ),
    ]