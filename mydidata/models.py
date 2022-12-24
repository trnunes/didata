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
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import html
import difflib


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
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id =  models.CharField(max_length=100, blank=True, verbose_name="Matrícula")
    def __str__(self):
        return self.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        profile = instance.profile
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
    instance.profile.save()

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

class GradingStrategy(object):
    def calculate(self, questions, students, test=None):
        students_grades = []
        answers_texts = []
        for student in students:
            for q in questions:
                if test:
                    answer = Answer.objects.filter(student=student, question=q, test=test).first()
                else:
                    answer = Answer.objects.filter(student=student, question=q).first()
                
                if answer and answer.answer_text:
                    answers_texts.append(answer.text_escaped())

        for student in students:
            sum_grades = 0
            sum_weights = 0
            
            for q in questions:
                if test:
                    answer = Answer.objects.filter(student=student, question=q, test=test).first()
                else:
                    answer = Answer.objects.filter(student=student, question=q).first()
                a_grade = 0
                if answer:
                    answer.correct()
                    a_grade = answer.grade
                    if answer.answer_text and q.punish_copies:
                        if answers_texts.count(answer.text_escaped()) > 1:
                            a_grade = a_grade*(1-(q.punishment_percent/100))
                sum_grades += a_grade
                sum_weights += q.weight
            
            if sum_weights: 
                wavg = sum_grades/sum_weights        
            students_grades.append([student,  wavg*10])
        return students_grades

class Topic(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    topic_title = models.CharField(max_length=200, verbose_name="Título")
    label = models.CharField(verbose_name="Rótulo", max_length=200, blank=True, null=True)
    topic_content = RichTextUploadingField(blank=True, null=True, verbose_name="Conteúdo")
    description = models.TextField(verbose_name="Descrição", default="Conteúdo relacionado à informática básica, técnicas de programação, desenvolvimento de apps")
    order = models.IntegerField(verbose_name="Ordem")
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Dono")
    discipline = models.ForeignKey(Discipline, null=True, on_delete=models.DO_NOTHING, verbose_name="Disciplina Associada")
    is_resource = models.BooleanField(default=False,verbose_name="É para reforço?")
    is_assessment = models.BooleanField(default=False)
    weight = models.PositiveSmallIntegerField(default=1, verbose_name="Peso")
    show_questions = models.BooleanField(default=True)
    has_assessment_question = models.BooleanField(default=True, verbose_name="Possui questão avaliativa?")
    enabled = models.BooleanField(default=True, verbose_name="Habilitado/Desabilitado")
    visible = models.BooleanField(default=True, verbose_name="Visível/Invisível")
    publish_date = models.DateTimeField(verbose_name="Data de Publicação", null=True, blank=True)
    thumbnail = models.ImageField(upload_to='images/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage(), verbose_name="Imagem de Capa")
    subject = models.CharField(max_length=200, verbose_name="Tópico", default="Variados")
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Tópicos'

    def __str__(self):
        return u"%s" % self.topic_title
    
    def text_escaped(self):
        return u'%s' % html.unescape(strip_tags(self.topic_content))
    
    def get_latest_approved_version(self):
        if not self.versions.exists():
            first_version = self.versions.create(content=self.topic_content, approved=True, user=self.owner, topic=self)
            return first_version
        
        return self.versions.filter(approved=True).order_by("-id").first()
    
    def sorted_versions(self):
        return self.versions.order_by("-id")


    def get_non_approved_versions(self):
        return []
    
    def update_to_version(self, id):
        version = self.versions.filter(pk=id).first()
        version.approved = True
        version.save()
        self.topic_content = version.content
        self.save()

    
    def next_url(self):
        topics = []
        topics.extend(self.discipline.topic_set.filter(visible=True).all())
        topics.sort(key=lambda topic: topic.order)
        self_index = topics.index(self)

        if self_index == len(topics) - 1:
            return '/mydidata/topics?discipline=' + self.discipline.uuid
        return reverse('mydidata:topic_detail', args=(topics[self_index + 1].uuid,))

    def previous_url(self):

        topics = []
        topics.extend(self.discipline.topic_set.filter(visible=True).all())
        topics.sort(key=lambda topic: topic.order)
        self_index = topics.index(self)
        if self_index == 0:
            return '/mydidata/topics?discipline=' + self.discipline.uuid

        return reverse('mydidata:topic_detail', args=(topics[self_index - 1].uuid,))

    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:topic_detail', [self.uuid]

    
    def get_absolute_url_questionary_anchor(self):
        return self.get_absolute_url() + "#cd-table"
    
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
    
    def get_deadline_for(self, classroom):
        deadlines = Deadline.objects.filter(topic=self, classroom=classroom)
        if not deadlines:
            return ""
        return deadlines.first().due_datetime
    
    def calculate_grades(self, classroom):
        grader = GradingStrategy()
        return grader.calculate(self.question_set.all(), classroom.students.all())
    
    def penalize_repeated(self):
        return []


class ContentVersion(models.Model, AdminURLMixin):
    content = RichTextUploadingField(verbose_name="Conteúdo")
    approved = models.BooleanField(default=False)
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, verbose_name="Tópico", related_name="versions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário", )

    def get_edit_url(self):
        return reverse("mydidata:version_edit", args=(self.id,))
    
    def get_detail_url(self):
        return reverse("mydidata:version_detail", args=(self.id,))
    
    def get_diff_url(self):
        return reverse("mydidata:version_compare", args=(self.id,))

    def replace_topic(self):
        self.approved = True
        self.topic.topic_content = self.content
        self.topic.save()
        self.save()
        
    def diff(self):
        htmlDiffer = difflib.HtmlDiff()
        text = self.content.splitlines()
        topic_text = self.topic.topic_content.splitlines()

        diffHtml = htmlDiffer.make_file(text, topic_text)
        diffHtml = diffHtml.replace("Legends", "Legenda")
        diffHtml = diffHtml.replace("Colors", "Cores")
        diffHtml = diffHtml.replace("Added", "Adicionado")
        diffHtml = diffHtml.replace("Changed", "Alterado")
        diffHtml = diffHtml.replace("Deleted", "Deletado")


        return diffHtml

        
    
    def text_escaped(self):
        return u'%s' % html.unescape(strip_tags(self.content))

    def __str__(self):
        return self.topic.topic_title + "." +str(self.id)

class Test(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    title = models.CharField(max_length=200, default="test", verbose_name="Título")
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, verbose_name="Tópico")
    limit_per_try = models.IntegerField(default=5)
    max_tries = models.IntegerField(default=2, verbose_name="Tentativas")
    key = models.CharField(max_length=200, default="testkey", verbose_name="Frase de Envio")
    class Meta:
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return u"%s" % self.title

    def is_closed(self, classroom):
        return self in classroom.closed_tests.all()

    def is_closed_for(self, user):

        test_user = TestUserRelation.objects.filter(test=self, student=user).first()
        classrooms = Classroom.objects.filter(students__id = user.id)
        for klass in classrooms:
            if self.is_closed(klass):
                return True
        
        return (test_user and test_user.is_closed)
    
    def get_answers(self, student):
        return Answer.objects.filter(student=student, question__id__in=self.get_ordered_questions(), test=self)

    def close_for(self, student):
        test_user = self.get_or_create_test_user_relation(student)
        test_user.is_closed = True
        test_user.save()

        

    def get_or_create_test_user_relation(self, user):
        test_user = TestUserRelation.objects.filter(student=user, test=self).first()
        if not test_user:
            test_user = TestUserRelation.objects.create(student=user, test=self)
            test_user.generate_question_index()
            test_user.save()
        return test_user
    
    def has_next_try(self, user):
        return self.get_or_create_test_user_relation(user).tries < self.max_tries
    
    def next_try(self, student):
        if not self.has_next_try(student):
            raise Exception("Amount of tries exceeded the limit: %s"%self.max_tries)

        test_user_rel = self.get_or_create_test_user_relation(student)
        self.get_answers(student).delete()
        test_user_rel.tries += 1
        test_user_rel.save()
        return test_user_rel.tries
    
    def next_question(self, user, question):
        if self.is_closed_for(user):
            return None
        tu = self.get_or_create_test_user_relation(user)
        current_questions = tu.current_questions()
        question_index = current_questions.index(question)

        if question_index < len(current_questions) - 1:
            return current_questions[question_index + 1]
        return None 
        
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
    
    def calculate_grades(self, classroom, students = []):
        grader = GradingStrategy()
        grades_by_student = {}
        if not students:
            students = classroom.students.all().order_by('first_name')
        
        for student in students:
            test_user = TestUserRelation.objects.filter(test=self, student=student).first()
            grades_by_student[student] = {}
            if test_user:
                student_grade = grader.calculate(test_user.current_questions(), [student], self)[0]
                grades_by_student[student]['grade'] = student_grade[1]
                grades_by_student[student]['test_user'] = test_user
                if student_grade[1] < 6:
                    if self.has_next_try(test_user.student):
                        grades_by_student[student]['next_try_link'] = reverse('mydidata:next_try', args=(test_user.id,))
            else:
                grades_by_student[student]['grade'] = "?"
        return grades_by_student


class Classroom(models.Model):
    uuid = ShortUUIDField(unique=True)
    academic_site_id = models.IntegerField(verbose_name = "Identificador no Acadêmico", default=0)
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
    
    def get_answers_for_topic(self, topic):
        questions = topic.get_ordered_questions()
        answers = []
        for q in questions:
            answers += list(Answer.objects.filter(question = q, student__id__in=[s.id for s in self.students.all()]))
        
        return answers
    
    

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
    ref_keywords = models.TextField(verbose_name="Palavras-Chave", blank=True)
    file_types_accepted = models.CharField(max_length=255, verbose_name="Tipos de arquivos aceitos", null=True, blank="True")
    text_required = models.BooleanField(default=False, verbose_name='Resposta de texto obrigatória?')
    weight = models.PositiveSmallIntegerField(default=1, verbose_name='Peso')
    file_upload_only = models.BooleanField(default=False, verbose_name="Aceitar somente upload de arquivos?")
    punish_copies = models.BooleanField(default=False,verbose_name="punir cópias exatas?")
    punishment_percent = models.PositiveSmallIntegerField(default=30, verbose_name="Percentual da Punição")
    test_inputs = models.CharField(null=True, blank=True, max_length=255, verbose_name = "entrada separa por vírgulas")
    expected_output = models.CharField(null=True, blank=True, max_length=255, verbose_name = "saída esperada do programa (ou parte)")

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

    def next_question_url(self):
        question = self.next_question()
        if question:
            return question.get_answer_url()
        return ""
        

    def next_question(self):
        ordered_questions = list(self.topic.get_ordered_questions())
        next_index = ordered_questions.index(self) + 1
        if next_index >= len(ordered_questions):
            return None
        return ordered_questions[next_index]
        
    def get_next_answer_for_student(self, student):
        question = self.next_question()
        answers = Answer.objects.filter(student=student, question=question)
        while question and not answers:
            question = question.next_question()
            answers = Answer.objects.filter(student=student, question=question)
        
        if not answers:
            return None
        return answers.first()
            
        

        




    def get_next_answer_url(self, student, test):
        if not student or not test:
            raise Exception("Student and Test refs cannot be null!")
        
        test_user_relation = TestUserRelation.objects.filter(student=student, test=test)
        if not test_user_relation:
            raise Exception("This user is not subscribed to this test")

        

        test_user_obj = test_user_relation[0]
        questions = test_user_obj.current_questions()
        self_index = questions.index([q for q in questions if q.uuid == self.uuid][0])
        
        if self_index == len(questions) - 1:
            return ""
        
        next_question = questions[self_index + 1]
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
    def get_answer_url_for_test(self, test):
        return 'mydidata:test_answer', (self.uuid, test.id)

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
    ALMOST_CORRECT = 5
    ALMOST_INCORRECT = 6
    ACCEPTABLE = 7
    STATUS_CHOICES = [
        (SENT, 'Enviada'),
        (UPDATED, 'Reenviada'),
    ]

    EVAL_CHOICES = [
        (CORRECT, 'Excelente! (1.0)'),
        (ALMOST_CORRECT, 'Quase Perfeita (0.8)'),
        (ACCEPTABLE, 'Aceitável (0.6)'),
        (ALMOST_INCORRECT, 'Apresenta muitos erros (0.3)'),
        (INCORRECT, 'Errada (0.0)'),
    ]

    answer_text = RichTextUploadingField(null=True, blank=True, verbose_name="Texto")
    assignment_file = models.FileField(upload_to='assignments/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage(), verbose_name="Arquivo")
    feedback = models.TextField(null=True, blank=True, verbose_name="Correções")
    status = models.IntegerField(choices=(STATUS_CHOICES + EVAL_CHOICES), default=SENT, verbose_name="Avaliação")
    grade = models.FloatField(default=0.0, verbose_name="Nota")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Questão")
    student = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Estudante")
    test = models.ForeignKey(Test, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Avaliação")
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Alternativa")
    comments = models.TextField(blank=True)
    

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

    def get_next_for_student(self):
        next_answer = self.question.get_next_answer_for_student(self.student)
        
        return next_answer
    
    def get_next_answer_for_class(self, classroom):

        students = list(classroom.students.all().order_by('first_name').all())
        next_answer = None
        for index, student in enumerate(students):
            if student.id == self.student.id and index < len(students):
                while not next_answer and index < len(students) - 1:
                    index += 1
                    next_answer = Answer.objects.filter(student=students[index], question=self.question).first()
                    if next_answer:
                        return reverse('mydidata:feedback', args=(next_answer.id,))

        return ""

    def multiple_choice_correct(self):
        correct_choice = self.question.choice_set.filter(is_correct=True).first()
        if correct_choice == self.choice:
            self.status = self.CORRECT
            self.grade = 1
        else:
            self.status = self.INCORRECT
            self.grade = 0
        self.save()

    def correct_c_programming_answer(self):
        import subprocess
        import os

        with open(str(self.id) + ".c", "w") as file:
            file.write(self.text_escaped().replace("\xa0", ""))

        r = subprocess.call(["gcc", "./"+str(self.id)+".c", "-o", str(self.id)])
        # 
        print("COMPILE RESULTS: ", r)
        if r == 1:
            os.remove("./" + str(self.id) + ".c")
            self.feedback = "A resposta possui erros de compilação. Corrija e envie novamente até a finalização do tópico!"
            return self.evaluate(self.INCORRECT)
        inputs = self.question.test_inputs.split(";")
        outputs = []
        for input in inputs:
            cmd = subprocess.Popen(['./' + str(self.id)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf8") 
            input = "\n".join([i.strip() for i in input.split(",")])
            output = cmd.communicate(input=input)
            outputs.append(output)
        
        os.remove("./" + str(self.id) + ".c")
        os.remove("./" + str(self.id))
        expected_outputs = self.question.expected_output.split(";")
        errors = []
        for expected, output in zip(expected_outputs, outputs):
            print("%s expected %s"%(output, expected))
            if expected not in str(output):
                print(" NOT FOUND: %s expected %s"%(output, expected))
                errors.append((input, expected))

        
        if not errors:
            self.feedback = "Programa passou nos testes!"
            return self.evaluate(self.CORRECT)
        
        error_str = ""
        for e in errors:
            error_str += "<br/>Entrada enviada: %s. Saída Esperada: %s"%(e[0], e[1])

        self.feedback = "Sua resposta compila corretamente mas apresenta erros de lógica." + error_str
        return self.evaluate(self.ALMOST_INCORRECT)

        
        
    def correct(self):
        # if self.question.expected_output:
            # return self.correct_c_programming_answer()
        if not self.question.is_discursive():
            return self.multiple_choice_correct()
        self.save()

    def is_correct(self):        
        self.status == self.CORRECT
    
    def is_ok(self):
        return self.status == self.CORRECT

    def is_updated(self):
        return self.status == self.UPDATED

    def is_sent(self):
        return self.status == self.SENT

    def evaluate(self, status):
        self.status = status
        if status == self.CORRECT:
            self.grade = 1.0
        if status == self.ALMOST_CORRECT:
            self.grade = 0.8
        if status == self.ACCEPTABLE:
            self.grade = 0.6
        if status == self.ALMOST_INCORRECT:
            self.grade = 0.3
        if status == self.INCORRECT:
            self.grade = 0.0
        self.save()
        
    def file_link(self):
         if self.assignment_file:
             return "<a href='%s' target=\"_blank\">Baixar o Arquivo da Resposta</a>" % (self.assignment_file.url,)
         else:
             return "Não possui arquivo"
    
    file_link.allow_tags = True

    def get_evaluation_message(self):
        return [c[1] for c in Answer.EVAL_CHOICES if c[0] == self.status]
    
    def get_answer_file_id(self):
        return self.student.first_name + "__" + self.student.last_name + "__" + str(self.student.id) + "__" + self.question.uuid
    
    @models.permalink
    def feedback_url(self):
        return "mydidata:feedback", [self.id]

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
    tries = models.IntegerField(default=1)
    key = models.CharField(max_length=255, verbose_name=_("Chave de Envio"), default="stub_key")
    class Meta:
        verbose_name_plural = 'Índices de Questões'
    
    def __str__(self):
        return str(self.student.first_name + " " + self.student.last_name + ": " + self.test.title)
    
    def index_list_as_array(self):
        print("INDEX_LIST:", self.index_list)
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


    def has_next_try_diff_questions(self):
        questions = list(self.test.questions.order_by('uuid').all())
        index_array = self.index_list_as_array()
        max_index = max(index_array)    
        if max_index == len(questions):
            return False
        return True

    def next_try_diff_questions(self):
        
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

class Deadline(models.Model, AdminURLMixin):
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, verbose_name="Tópico")
    classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
    due_datetime = models.DateTimeField()
    
    def __str__(self):
        return "%s para %s vence em %s"%(self.topic.topic_title, self.classroom.name, self.get_local_due_date())

    def get_local_due_date(self):
        return timezone.localtime(self.due_datetime).strftime("%d/%m/%Y às %H:%M:%S")

    def datetime_to_str(self):
        formatedDate = self.due_datetime.strftime("%d/%m/%Y às %H:%M:%S")
        return formatedDate

