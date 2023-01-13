# Generated by Django 2.0.2 on 2022-12-31 12:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0062_remove_contentversion_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choice',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='mydidata.Question', verbose_name='Questão'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='students',
            field=models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL, verbose_name='Estudantes'),
        ),
    ]