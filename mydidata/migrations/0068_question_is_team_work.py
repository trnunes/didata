# Generated by Django 2.0.2 on 2023-01-11 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0067_team_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_team_work',
            field=models.BooleanField(default=False, verbose_name='É trabalho em equipe? (somente equipes podem enviar)'),
        ),
    ]
