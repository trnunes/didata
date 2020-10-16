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
from django.utils.html import strip_tags
import html

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
    students = models.ManyToManyField(User, verbose_name="Estudantes", null=True, blank=True,)
    enabled = models.BooleanField(default=True, verbose_name="Habilitado?")
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
    show_questions = models.BooleanField(default=True)
    has_assessment_question = models.BooleanField(default=True, verbose_name="Possui questão avaliativa?")
    
    class Meta:
        verbose_name_plural = 'Tópicos'

    def __str__(self):
        return u"%s" % self.topic_title
    
    
    def next_url(self):
        topics = []
        topics.extend(self.discipline.topic_set.all())
        topics.sort(key=lambda topic: topic.order)
        self_index = topics.index(self)

        if self_index == len(topics) - 1:
            return '/mydidata/topics?discipline=' + self.discipline.uuid
        return reverse('mydidata:topic_detail', args=(topics[self_index + 1].uuid,))

    def previous_url(self):

        topics = []
        topics.extend(self.discipline.topic_set.all())
        topics.sort(key=lambda topic: topic.order)
        self_index = topics.index(self)
        if self_index == 0:
            return '/mydidata/topics?discipline=' + self.discipline.uuid

        return reverse('mydidata:topic_detail', args=(topics[self_index - 1].uuid,))

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
    limit_per_try = models.IntegerField(default=5)
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

    def questions_range(self):
        return range(self.limit_per_try)

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
    index = models.PositiveSmallIntegerField(default=1, verbose_name='Ordem')
    question_text = RichTextUploadingField(verbose_name='Texto')    
    file_types_accepted = models.CharField(max_length=255, verbose_name="Tipos de arquivos aceitos", null=True, blank="True")
    text_required = models.BooleanField(default=False, verbose_name='Resposta de texto obrigatória?')
    weight = models.PositiveSmallIntegerField(default=1, verbose_name='Peso')
    file_upload_only = models.BooleanField(default=False, verbose_name="Aceitar somente upload de arquivos?")

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
    
    class Meta:
        verbose_name_plural = 'Questões'

    def __str__(self):

        return u'%s ...' % html.unescape(strip_tags(self.question_text))[0:200]
    
    def text_escaped(self):
        return u'%s' % html.unescape(strip_tags(self.question_text))

    def is_discursive(self):
        return len(self.choice_set.all()) == 0

    def get_answer_for(self, student_list):
        answers = list(Answer.objects.filter(question = self, student__id__in=[s.id for s in student_list]))
        
        if not answers:
            for student in student_list:
                answer = Answer.objects.create(student = student, question=self)
                answer.save()
                answers.append(answer)
        
        return answers

    def get_next_answer_url(self, student, test):
        if not student or not test:
            raise Exception("Student and Test refs cannot be null!")
        
        test_user_relation = TestUserRelation.objects.filter(student=student, test=test)
        if not test_user_relation:
            raise Exception("This user is not subscribed to this test")

        

        test_user_obj = test_user_relation[0]
        questions = test_user_obj.current_questions()
        print("Current Question: ", self.uuid)
    
        print("Next Answer questions: ", [q.uuid for q in questions])
        self_index = questions.index([q for q in questions if q.uuid == self.uuid][0])
        
        if self_index == len(questions) - 1:
            return ""
        
        next_question = questions[self_index + 1]
        print("Next Question: ", next_question.uuid)
        return next_question.get_answer_url(test)


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
        
        if self.is_discursive():
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
    # choice_text = RichTextUploadingField(verbose_name='Texto da Alternativa')
    choice_text = models.TextField()
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

    answer_text = RichTextUploadingField(null=True, blank=True, verbose_name="Texto")
    assignment_file = models.FileField(upload_to='assignments/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage(), verbose_name="Arquivo")
    feedback = RichTextUploadingField(null=True, blank=True, verbose_name="Correções")
    status = models.IntegerField(choices=STATUS_CHOICES, default=SENT, verbose_name="Avaliação")
    grade = models.FloatField(default=0.0, verbose_name="Nota")
    question = models.ForeignKey(Question, on_delete=models.DO_NOTHING, verbose_name="Questão")
    student = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Estudante")
    test = models.ForeignKey(Test, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Avaliação")
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Alternativa")

    class Meta:
        verbose_name_plural = 'Respostas'
    
    @classmethod
    def find(cls, student, question, test_id=None):
        args = {'student': student, 'question': question}
        if test_id:
            args['test'] = Test.objects.get(pk=test_id)
        return cls.objects.filter(**args).first()

    def __str__(self):
        full_name = self.student.first_name + " " + self.student.last_name
        return "Answer of %s for %s" % (full_name, str(self.question))

    def text_escaped(self):
        return u'%s' % html.unescape(strip_tags(self.answer_text))

    def multiple_choice_correct(self):
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

    def correct(self):
        if not self.question.is_discursive():
            return self.multiple_choice_correct()

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

    def file_link(self):
         if self.assignment_file:
             return "<a href='%s' target=\"_blank\">Baixar o Arquivo da Resposta</a>" % (self.assignment_file.url,)
         else:
             return "Não possui arquivo"
    
    file_link.allow_tags = True

    def get_answer_file_id(self):
        return self.student.first_name + "__" + self.student.last_name + "__" + str(self.student.id) + "__" + self.question.uuid
    
    @models.permalink
    def get_detail_url(self):
        if not self.question.is_discursive():
            return "mydidata:multiple_choice_answer_detail", [self.id]
        else:
            return "mydidata:discursive_answer_detail", [self.id]

class OverwriteStorage(FileSystemStorage):
    '''
    Muda o comportamento padrão do Django e o faz sobrescrever arquivos de
    mesmo nome que foram carregados pelo usuário ao invés de renomeá-los.
    '''
    def get_available_name(self, name,  max_length=None):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
        
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

    def generate_question_index(self):
        import random
        questions = list(self.test.questions.order_by('uuid').all())[0:self.test.limit_per_try]
        index_list = [questions.index(q)+1 for q in questions]
        random.shuffle(index_list)
        self.set_index_list(index_list)
        return index_list
    
    def current_questions(self):
        index_array = self.index_list_as_array()
        return [list(self.test.questions.order_by('uuid'))[i-1] for i in index_array ]

    def has_next_try(self):
        questions = list(self.test.questions.order_by('uuid').all())
        index_array = self.index_list_as_array()
        max_index = max(index_array)    
        if max_index == len(questions):
            return False
        return True

    def next_try(self):
        
        questions = list(self.test.questions.order_by('uuid').all())
        question_index_array = [questions.index(q)+1 for q in questions]

        test_size = self.test.limit_per_try

        index_array = self.index_list_as_array()
        max_index = max(index_array)
    
        if max_index == len(questions):
            return ""

        try_questions = question_index_array[max_index:(max_index+test_size)]
        
        import random
        random.shuffle(try_questions)
        self.set_index_list(try_questions)
        self.is_closed = False
        self.save()

        return questions[try_questions[0]-1].get_answer_url(self.test)



    def set_index_list(self, index_list):
        self.index_list = str(index_list)

