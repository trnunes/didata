# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-12 23:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0019_choice_is_correct'),
    ]

    operations = [
        migrations.RenameField(
            model_name='answer',
            old_name='user',
            new_name='student',
        ),
    ]
