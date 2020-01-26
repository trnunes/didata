# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models
from django.contrib.auth.models import User
from shortuuidfield import ShortUUIDField
from ckeditor_uploader.fields import RichTextUploadingField
from django import template
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.translation import gettext as _
from mydidata.storage_backends import PublicMediaStorage
import urllib
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.validators import FileExtensionValidator
import random

class AdminURLMixin(object):
    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (
            content_type.app_label,
            content_type.model),
            args=(self.id,))


# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

# Create your models here.
# class User(models.Model):
#     user_name = models.CharField(max_length=200)

class Discipline(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    name = models.CharField(max_length=255, verbose_name="Nome",)
    students = models.ManyToManyField(User, verbose_name="Estudantes",)
    class Meta:
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return u"%s" % self.name
        
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:discipline_detail', [self.uuid]

class Topic(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    topic_title = models.CharField(max_length=200, verbose_name="Título")
    topic_content = RichTextUploadingField(blank=True, null=True, verbose_name="Conteúdo")
    order = models.IntegerField(verbose_name="Ordem")
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Dono")
    discipline = models.ForeignKey(Discipline, null=True, on_delete=models.DO_NOTHING, verbose_name="Disciplina Associada")
    is_resource = models.BooleanField(default=False,verbose_name="É para reforço?")
    is_assessment = models.BooleanField(default=False)
    weight = models.PositiveSmallIntegerField(default=1, verbose_name="Peso")

    class Meta:
        verbose_name_plural = 'Tópicos'

    def __str__(self):
        return u"%s" % self.topic_title

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:topic_detail', [self.uuid]

    @models.permalink
    def get_update_url(self):
        return 'mydidata:topic_update', [self.uuid]

    @models.permalink
    def get_delete_url(self):
        return 'mydidata:topic_delete', [self.uuid]

    @models.permalink
    def get_close_url(self, klass):
        return 'mydidata:topic_close', [self.uuid, klass.id]
    
    def get_ordered_questions(self):
        return self.question_set.all().order_by('index')

class Test(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    title = models.CharField(max_length=200, default="test", verbose_name="Título")
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, verbose_name="Tópico")
    key = models.CharField(max_length=200, default="testkey", verbose_name="Frase de Envio")
    class Meta:
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return u"%s" % self.title

    def is_closed(self, classroom):
        return self in classroom.closed_tests.all()

    def is_closed_for(self, user):
        test_user = TestUserRelation.objects.filter(test=self, student=user).first()
        return (test_user and test_user.is_closed)

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:test_detail', [self.uuid]

    @models.permalink
    def get_update_url(self):
        return 'mydidata:test_update', [self.uuid]

    @models.permalink
    def get_delete_url(self):
        return 'mydidata:test_delete', [self.uuid]

    @models.permalink
    def get_close_url(self, klass):
        return 'mydidata:test_close', [self.uuid, klass.id]

    @models.permalink
    def get_progress_url(self, klass):
        return 'mydidata:test_progress', [self.uuid, klass.id]
    
    def get_ordered_questions(self):
        return self.questions.order_by('index').all()

class Classroom(models.Model):
    uuid = ShortUUIDField(unique=True)
    name = models.CharField(max_length=255, verbose_name="Nome")
    students = models.ManyToManyField(User, null=True, verbose_name="Estudantes")
    disciplines = models.ManyToManyField(Discipline, null=True, verbose_name="Disciplinas")
    closed_topics = models.ManyToManyField(Topic, null=True, blank=True, verbose_name="Tópicos Fechados")
    closed_tests = models.ManyToManyField(Test, null=True, blank=True, related_name="closed_tests", verbose_name="Avaliações Fechadas")
    tests = models.ManyToManyField(Test, null=True, blank=True, verbose_name="Avaliações")

    class Meta:
        verbose_name_plural = 'Turmas'

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:class_progress', [self.id]

    @models.permalink
    def get_percentage_progress_url(self):
        return 'mydidata:percentage_progress', [self.id]

    @models.permalink
    def get_grades_url(self):
        return 'mydidata:calculate_grades', [self.id]

    @models.permalink
    def get_signup_link(self):
        return 'mydidata:sub_new', [self.id]

    def __str__(self):
        return u"%s" % self.name
        
    def topic_is_closed(self, topic):
        return topic in self.closed_topics.all()

    def is_test_closed(self, test):
        return test in self.closed_tests.all()

    def in_class(self, test):
        return test in self.tests.all()

class ResourceRoom(models.Model):
    uuid = ShortUUIDField(unique=True)
    name = models.CharField(max_length=255, verbose_name='Nome')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name='Turma')
    students = models.ManyToManyField(User, null=True, verbose_name='Alunos')
    topics = models.ManyToManyField(Topic, null=True, verbose_name='Tópicos')
    class Meta:
        verbose_name_plural = 'Turmas de Reforço'

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:resource_room_progress', [self.uuid]

    @models.permalink
    def get_percentage_progress_url(self):
        return 'mydidata:percentage_progress', [self.id]

class Question(models.Model):
    uuid = ShortUUIDField(unique=True)
    index = models.PositiveSmallIntegerField(verbose_name='Ordem')
    question_text = RichTextUploadingField(verbose_name='Texto')
    is_discursive = models.BooleanField(default=False, verbose_name='É discursiva?')
    file_types_accepted = models.CharField(max_length=255, verbose_name="Tipos de arquivos aceitos", null=True, blank="True")
    text_required = models.BooleanField(default=False, verbose_name='Resposta de texto obrigatória?')
    weight = models.PositiveSmallIntegerField(default=1, verbose_name='Peso')

    DIFFICULTY_LIST = (
        (1, 'Difícil'),
        (2, 'Médio'),
        (3, 'Fácil'),
    )
    difficulty_level = models.PositiveSmallIntegerField(choices=DIFFICULTY_LIST, verbose_name="Dificuldade")
    TYPE_LIST = (
        (1, "Exercício"),
        (2, "Trabalho"),
        (3, "Prova")
    )
    question_type = models.PositiveSmallIntegerField(choices=TYPE_LIST, verbose_name="Tipo")
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, null=True, blank=True)
    #TODO change to many-to-many
    tests = models.ManyToManyField(Test, null=True, blank=True, related_name="questions", verbose_name="Avaliações",)
    test = models.ForeignKey(Test, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Questões'

    def __str__(self):
        return u'%s ...' % self.question_text[0:100]

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:question_detail', [self.uuid]

    @models.permalink
    def get_update_url(self):
        return 'mydidata:question_update', [self.uuid]

    @models.permalink
    def get_delete_url(self):
        return 'mydidata:question_delete', [self.id]
        
    @models.permalink
    def get_answer_url(self, test=None):
        params = [self.uuid]
        if test:
            params.append(test.id)
        
        if self.is_discursive:
            return 'mydidata:discursive_answer', params
        else:
            return 'mydidata:multiple_choice_answer', params

    
    @models.permalink
    def get_test_url(self):
        return 'mydidata:test_for', [self.uuid]

    def shuffled_choice_set(self):
        choice_list = list(self.choice_set.all())
        random.shuffle(choice_list)
        return choice_list

      
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Questão")
    choice_text = models.CharField(max_length=200, verbose_name="Texto")
    is_correct = models.BooleanField(default=False, verbose_name="É a alternativa correta?")
    class Meta:
        verbose_name_plural = 'Alternativas'
        
    def __str__(self):
        return u'%s' % self.choice_text

class Answer(models.Model):
    SENT = 1
    CORRECT = 2
    INCORRECT = 3
    UPDATED = 4
    STATUS_CHOICES = (
        (SENT, 'Enviada'),
        (CORRECT, 'Correta'),
        (INCORRECT, 'Incorreta'),
        (UPDATED, 'Reenviada'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=SENT, verbose_name="Avaliação")
    grade = models.FloatField(default=0.0, verbose_name="Nota")
    question = models.ForeignKey(Question, on_delete=models.DO_NOTHING, verbose_name="Questão")
    student = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Estudante")
    test = models.ForeignKey(Test, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Avaliação")
    
    class Meta:
        verbose_name_plural = 'Respostas'

    def correct(self):
        self.status = self.CORRECT
        if not self.grade:
            self.grade = 1
        self.save()

    def is_correct(self):        
        self.status == self.CORRECT

    def is_ok(self):
        return self.status == self.CORRECT

    def is_updated(self):
        return self.status == self.UPDATED

    def is_sent(self):
        return self.status == self.SENT

    def get_answer_file_id(self):
        return self.student.first_name + "__" + self.student.last_name + "__" + str(self.student.id) + "__" + self.question.uuid



class MultipleChoiceAnswer(Answer):
    choice = models.ForeignKey(Choice, null=True, on_delete=models.DO_NOTHING, verbose_name="Alternativa")
    class Meta:
        verbose_name_plural = 'Respostas de Múltipla Escolha'

    def correct(self):
        correct_choice = self.question.choice_set.filter(is_correct=True).first()
        print("CORRECT: ",  correct_choice)
        print("ACTUAL: ",  self.choice)
        if correct_choice == self.choice:
            self.status = self.CORRECT
            self.grade = 1
        else:
            self.status = self.INCORRECT
            self.grade = 0
        self.save()
    
    @models.permalink
    def get_detail_url(self):
        return "mydidata:multiple_choice_answer_detail", [self.id]

class OverwriteStorage(FileSystemStorage):
    '''
    Muda o comportamento padrão do Django e o faz sobrescrever arquivos de
    mesmo nome que foram carregados pelo usuário ao invés de renomeá-los.
    '''
    def get_available_name(self, name,  max_length=None):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
        
class DiscursiveAnswer(Answer):
    answer_text = RichTextUploadingField(null=True, blank=True, verbose_name="Texto")
    assignment_file = models.FileField(upload_to='assignments/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage(), verbose_name="Arquivo")
    feedback = RichTextUploadingField(null=True, blank=True, verbose_name="Correções")


    class Meta:
        verbose_name_plural = 'Respostas Discursivas'

    def __str__(self):
        return str(self.question.index)

    def file_link(self):
         if self.assignment_file:
             return "<a href='%s' target=\"_blank\">Baixar o Arquivo da Resposta</a>" % (self.assignment_file.url,)
         else:
             return "No attachment"
    file_link.allow_tags = True
             
    @models.permalink
    def get_detail_url(self):
        return "mydidata:discursive_answer_detail", [self.id]

class TestUserRelation(models.Model):
    student = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    test = models.ForeignKey(Test, on_delete=models.DO_NOTHING)
    index_list = models.CharField(max_length=255, verbose_name=_("índices"),)
    is_closed = models.BooleanField(default=False)
    key = models.CharField(max_length=255, verbose_name=_("Chave de Envio"), default="stub_key")
    class Meta:
        verbose_name_plural = 'Índices de Questões'
    def __str__(self):
        return str(self.student.first_name + " " + self.student.last_name + ": " + self.test.title)
    def index_list_as_array(self):
        return eval(self.index_list)
    def set_index_list(self, index_list):
        self.index_list = str(index_list)

