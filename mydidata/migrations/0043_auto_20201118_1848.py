# Generated by Django 2.0.2 on 2020-11-18 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0042_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mydidata.Question', verbose_name='Questão'),
        ),
    ]