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
    name = models.CharField(max_length=255, verbose_name=_("Name"),)
    students = models.ManyToManyField(User, verbose_name=_("Students"),)
    class Meta:
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return u"%s" % self.name
        
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:discipline_detail', [self.uuid]

class Topic(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    topic_title = models.CharField(max_length=200)
    topic_content = RichTextUploadingField(blank=True, null=True)
    order = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    discipline = models.ForeignKey(Discipline, null=True, on_delete=models.DO_NOTHING)    
    is_resource = models.BooleanField(default=False)
    is_assessment = models.BooleanField(default=False)
    weight = models.PositiveSmallIntegerField(default=1)

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
    title = models.CharField(max_length=200, default="test")
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return u"%s" % self.title

    def is_closed(self, classroom):
        return self in classroom.closed_tests.all()
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
        return self.question_set.all().order_by('index')

class Classroom(models.Model):
    uuid = ShortUUIDField(unique=True)
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(User, null=True)
    disciplines = models.ManyToManyField(Discipline, null=True)
    closed_topics = models.ManyToManyField(Topic, null=True, blank=True)
    closed_tests = models.ManyToManyField(Test, null=True, blank=True, related_name="closed_tests")
    tests = models.ManyToManyField(Test, null=True, blank=True)

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
    name = models.CharField(max_length=255)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, null=True)
    topics = models.ManyToManyField(Topic, null=True)
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
    index = models.PositiveSmallIntegerField()
    question_text = RichTextUploadingField()
    is_discursive = models.BooleanField(default=False)
    file_types_accepted = models.CharField(max_length=255, verbose_name=_("Types"), null=True, blank="True")
    text_required = models.BooleanField(default=False)
    weight = models.PositiveSmallIntegerField(default=1)

    DIFFICULTY_LIST = (
        (1, 'Difícil'),
        (2, 'Médio'),
        (3, 'Fácil'),
    )   
    difficulty_level = models.PositiveSmallIntegerField(choices=DIFFICULTY_LIST)
    TYPE_LIST = (
        (1, "Exercício"),
        (2, "Trabalho"),
        (3, "Prova")
    )
    question_type = models.PositiveSmallIntegerField(choices=TYPE_LIST)
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, null=True, blank=True)
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
    def get_answer_url(self):
        if self.is_discursive:
            return 'mydidata:discursive_answer', [self.uuid]
        else:
            return 'mydidata:multiple_choice_answer', [self.uuid]
    
    @models.permalink
    def get_test_url(self):
        return 'mydidata:test_for', [self.uuid]
      
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
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
    status = models.IntegerField(choices=STATUS_CHOICES, default=SENT)
    grade = models.FloatField(default=0.0)
    question = models.ForeignKey(Question, on_delete=models.DO_NOTHING)
    student = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    test = models.ForeignKey(Test, null=True, blank=True, on_delete=models.DO_NOTHING)
    
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
    choice = models.ForeignKey(Choice, null=True, on_delete=models.DO_NOTHING)
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
    answer_text = RichTextUploadingField(null=True, blank=True)
    assignment_file = models.FileField(upload_to='assignments/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage())
    feedback = RichTextUploadingField(null=True, blank=True)


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

