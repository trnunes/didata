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
# Create your models here.
# class User(models.Model):
#     user_name = models.CharField(max_length=200)

class Discipline(models.Model):
    uuid = ShortUUIDField(unique=True)
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(User)
    class Meta:
        verbose_name_plural = 'Disciplinas'

    def __unicode__(self):
        return u"%s" % self.name
        
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:discipline_detail', [self.uuid]

class Topic(models.Model):
    uuid = ShortUUIDField(unique=True)
    topic_title = models.CharField(max_length=200)
    topic_content = RichTextUploadingField()
    order = models.IntegerField()
    owner = models.ForeignKey(User)
    discipline = models.ForeignKey(Discipline, null=True)
    class Meta:
        verbose_name_plural = 'Tópicos'

    def __unicode__(self):
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
        

class Question(models.Model):
    uuid = ShortUUIDField(unique=True)
    index = models.PositiveSmallIntegerField()
    question_text = RichTextUploadingField()
    is_discursive = models.BooleanField(default=False)
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
    topic = models.ForeignKey(Topic)
    class Meta:
        verbose_name_plural = 'Questões'

    def __unicode__(self):
        return u'%s' % self.question_text

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
            
                
        
        

      
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=True)
    class Meta:
        verbose_name_plural = 'Alternativas'
        
    def __unicode__(self):
        return u'%s' % self.choice_text

class Test(models.Model):
    uuid = ShortUUIDField(unique=True)
    student = models.ForeignKey(User)
    questions = models.ManyToManyField(Question)
    topic = models.ForeignKey(Topic)
    DIFFICULTY_LIST = (
        (1, 'Difícil'),
        (2, 'Médio'),
        (3, 'Fácil'),
        (4, 'Misto'),
    )
    difficulty_level = models.PositiveSmallIntegerField(choices=DIFFICULTY_LIST)
  
class Answer(models.Model):
    question = models.ForeignKey(Question)
    student = models.ForeignKey(User)
    test = models.ForeignKey(Test, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Respostas'
    def is_correct(self):
        return False
    
    def get_answer_file_id(self):
        return self.student.first_name + "__" + self.student.last_name + "__" + str(self.student.id) + "__" + self.question.uuid

class MultipleChoiceAnswer(Answer):
    choice = models.ForeignKey(Choice, null=True)
    class Meta:
        verbose_name_plural = 'Respostas de Múltipla Escolha'
        
    def is_correct(self):
        correct_choice = self.question.choice_set.filter(is_correct=True)[0]
        if(correct_choice == self.choice):
            return True
        else:
            return False
    
    @models.permalink
    def get_detail_url(self):
        return "mydidata:multiple_choice_answer_detail", [self.id]

class OverwriteStorage(FileSystemStorage):
    '''
    Muda o comportamento padrão do Django e o faz sobrescrever arquivos de
    mesmo nome que foram carregados pelo usuário ao invés de renomeá-los.
    '''
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
        
class DiscursiveAnswer(Answer):
    answer_text = RichTextUploadingField(null=True, blank=True)
    assignment_file = models.FileField(upload_to='uploads/assignments/%Y/%m/%d', null=True, blank=True, storage=OverwriteStorage())
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Respostas Discursivas'

    def __unicode__(self):
        return str(self.question.index)
        
    @models.permalink
    def get_detail_url(self):
        return "mydidata:discursive_answer_detail", [self.id]

    
