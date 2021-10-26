# Generated by Django 2.0.2 on 2021-10-23 19:58

from django.db import migrations, models
import mydidata.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0047_auto_20210312_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='publish_date',
            field=models.DateTimeField(null=True, verbose_name='Data de Publicação'),
        ),
        migrations.AddField(
            model_name='topic',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, storage=mydidata.storage_backends.PublicMediaStorage(), upload_to='images/%Y/%m/%d', verbose_name='Imagem de Capa'),
        ),
    ]
