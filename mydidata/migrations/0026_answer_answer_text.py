# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-12-22 19:35
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0025_auto_20171221_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='answer_text',
            field=ckeditor_uploader.fields.RichTextUploadingField(default=''),
            preserve_default=False,
        ),
    ]
