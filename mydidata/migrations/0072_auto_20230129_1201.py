# Generated by Django 2.0.2 on 2023-01-29 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0071_auto_20230125_1014'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='discipline',
            name='students',
        ),
        migrations.AddField(
            model_name='profile',
            name='actions_log',
            field=models.TextField(blank=True, null=True, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='test',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='answers', to='mydidata.Test', verbose_name='Avaliação'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='closed_tests',
            field=models.ManyToManyField(blank=True, null=True, related_name='closed_for_classrooms', to='mydidata.Test', verbose_name='Avaliações Fechadas'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='tests',
            field=models.ManyToManyField(blank=True, null=True, related_name='classrooms', to='mydidata.Test', verbose_name='Avaliações'),
        ),
        migrations.AlterField(
            model_name='testuserrelation',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_user_relations', to='mydidata.Test'),
        ),
    ]