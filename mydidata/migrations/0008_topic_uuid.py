# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-05 16:56
from __future__ import unicode_literals

from django.db import migrations
import shortuuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0007_answer_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='uuid',
            field=shortuuidfield.fields.ShortUUIDField(blank=True, editable=False, max_length=22, unique=True),
        ),
    ]