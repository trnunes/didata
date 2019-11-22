# Generated by Django 2.0.2 on 2019-11-22 22:15

import ckeditor_uploader.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mydidata.storage_backends


class Migration(migrations.Migration):

    dependencies = [
        ('mydidata', '0028_testuserrelation_is_closed'),
    ]

    operations = [
        migrations.AddField(
            model_name='testuserrelation',
            name='key',
            field=models.CharField(default='stub_key', max_length=255, verbose_name='Chave de Envio'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='grade',
            field=models.FloatField(default=0.0, verbose_name='Nota'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='mydidata.Question', verbose_name='Questão'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='status',
            field=models.IntegerField(choices=[(1, 'Enviada'), (2, 'Correta'), (3, 'Incorreta'), (4, 'Reenviada')], default=1, verbose_name='Avaliação'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='Estudante'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='test',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='mydidata.Test', verbose_name='Avaliação'),
        ),
        migrations.AlterField(
            model_name='choice',
            name='choice_text',
            field=models.CharField(max_length=200, verbose_name='Texto'),
        ),
        migrations.AlterField(
            model_name='choice',
            name='is_correct',
            field=models.BooleanField(default=False, verbose_name='É a alternativa correta?'),
        ),
        migrations.AlterField(
            model_name='choice',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mydidata.Question', verbose_name='Questão'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='closed_tests',
            field=models.ManyToManyField(blank=True, null=True, related_name='closed_tests', to='mydidata.Test', verbose_name='Avaliações Fechadas'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='closed_topics',
            field=models.ManyToManyField(blank=True, null=True, to='mydidata.Topic', verbose_name='Tópicos Fechados'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='disciplines',
            field=models.ManyToManyField(null=True, to='mydidata.Discipline', verbose_name='Disciplinas'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='students',
            field=models.ManyToManyField(null=True, to=settings.AUTH_USER_MODEL, verbose_name='Estudantes'),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='tests',
            field=models.ManyToManyField(blank=True, null=True, to='mydidata.Test', verbose_name='Avaliações'),
        ),
        migrations.AlterField(
            model_name='discipline',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='discipline',
            name='students',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Estudantes'),
        ),
        migrations.AlterField(
            model_name='discursiveanswer',
            name='answer_text',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='Texto'),
        ),
        migrations.AlterField(
            model_name='discursiveanswer',
            name='assignment_file',
            field=models.FileField(blank=True, null=True, storage=mydidata.storage_backends.PublicMediaStorage(), upload_to='assignments/%Y/%m/%d', verbose_name='Arquivo'),
        ),
        migrations.AlterField(
            model_name='discursiveanswer',
            name='feedback',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='Correções'),
        ),
        migrations.AlterField(
            model_name='multiplechoiceanswer',
            name='choice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='mydidata.Choice', verbose_name='Alternativa'),
        ),
        migrations.AlterField(
            model_name='question',
            name='difficulty_level',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Difícil'), (2, 'Médio'), (3, 'Fácil')], verbose_name='Dificuldade'),
        ),
        migrations.AlterField(
            model_name='question',
            name='file_types_accepted',
            field=models.CharField(blank='True', max_length=255, null=True, verbose_name='Tipos de arquivos aceitos'),
        ),
        migrations.AlterField(
            model_name='question',
            name='index',
            field=models.PositiveSmallIntegerField(verbose_name='Ordem'),
        ),
        migrations.AlterField(
            model_name='question',
            name='is_discursive',
            field=models.BooleanField(default=False, verbose_name='É discursiva?'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_text',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Texto'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Exercício'), (2, 'Trabalho'), (3, 'Prova')], verbose_name='Tipo'),
        ),
        migrations.AlterField(
            model_name='question',
            name='text_required',
            field=models.BooleanField(default=False, verbose_name='Resposta de texto obrigatória?'),
        ),
        migrations.AlterField(
            model_name='question',
            name='weight',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='Peso'),
        ),
        migrations.AlterField(
            model_name='resourceroom',
            name='classroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mydidata.Classroom', verbose_name='Turma'),
        ),
        migrations.AlterField(
            model_name='resourceroom',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='resourceroom',
            name='students',
            field=models.ManyToManyField(null=True, to=settings.AUTH_USER_MODEL, verbose_name='Alunos'),
        ),
        migrations.AlterField(
            model_name='resourceroom',
            name='topics',
            field=models.ManyToManyField(null=True, to='mydidata.Topic', verbose_name='Tópicos'),
        ),
        migrations.AlterField(
            model_name='test',
            name='title',
            field=models.CharField(default='test', max_length=200, verbose_name='Título'),
        ),
        migrations.AlterField(
            model_name='test',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='mydidata.Topic', verbose_name='Tópico'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='discipline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='mydidata.Discipline', verbose_name='Disciplina Associada'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='is_resource',
            field=models.BooleanField(default=False, verbose_name='É para reforço?'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='order',
            field=models.IntegerField(verbose_name='Ordem'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='Dono'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='topic_content',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='Conteúdo'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='topic_title',
            field=models.CharField(max_length=200, verbose_name='Título'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='weight',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='Peso'),
        ),
    ]
