# Generated by Django 2.0.2 on 2018-03-12 20:38

import ckeditor_uploader.fields
from django.conf import settings
from django.db import migrations, models
import mydidata.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0002_auto_20180221_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discipline',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='discipline',
            name='students',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Students'),
        ),
        migrations.AlterField(
            model_name='discursiveanswer',
            name='assignment_file',
            field=models.FileField(blank=True, null=True, storage=mydidata.storage_backends.PublicMediaStorage(), upload_to='assignments/%Y/%m/%d'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='topic_content',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
    ]