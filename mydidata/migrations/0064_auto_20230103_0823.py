# Generated by Django 2.0.2 on 2023-01-03 11:23

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0063_auto_20221231_0950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='difficulty_level',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Difícil'), (2, 'Médio'), (3, 'Fácil')], default=2, verbose_name='Dificuldade'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_text',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Enunciado da Questão'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Exercício'), (2, 'Trabalho'), (3, 'Prova')], default=1, verbose_name='Tipo'),
        ),
    ]