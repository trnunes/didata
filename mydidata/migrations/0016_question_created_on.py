# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-07 18:34
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0015_remove_question_created_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='created_on',
            field=models.DateField(default=datetime.datetime(2017, 12, 7, 18, 34, 48, 350223, tzinfo=utc)),
        ),
    ]