# Generated by Django 2.0.2 on 2019-05-27 15:27

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0003_auto_20180312_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='discursiveanswer',
            name='feedback',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
    ]