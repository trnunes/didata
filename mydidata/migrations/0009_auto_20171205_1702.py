# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-05 17:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0008_topic_uuid'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topic',
            options={'verbose_name_plural': 'topics'},
        ),
    ]
