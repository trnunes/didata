# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-02-08 20:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mydidata.models


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0035_auto_20180208_1549'),
    ]

    operations = [
        migrations.AddField(
            model_name='discursiveanswer',
            name='is_correct',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='answer',
            name='test',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mydidata.Test'),
        ),
        migrations.AlterField(
            model_name='discursiveanswer',
            name='assignment_file',
            field=models.FileField(blank=True, null=True, storage=mydidata.models.OverwriteStorage(), upload_to='uploads/assignments/%Y/%m/%d'),
        ),
    ]