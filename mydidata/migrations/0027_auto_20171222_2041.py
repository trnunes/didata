# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-22 20:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0026_answer_answer_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='choice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mydidata.Choice'),
        ),
    ]
