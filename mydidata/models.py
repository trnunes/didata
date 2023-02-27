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
from django.db.models import Avg, Q, Sum, F
from django.db.models.query import QuerySet
from django.core.mail import send_mail

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
    actions_log = models.TextField(verbose_name="Descrição", default="", blank=True, null=True)
    comment_points = models.IntegerField(verbose_name="Pontos Adquiridos em comentários", default = 0)
    answer_points = models.IntegerField(verbose_name="pontos adquiridos em respostas", default = 0)
    post_points = models.IntegerField(verbose_name="Pontos Adquiridos em Postagens no Fórum", default = 0)
    reply_points = models.IntegerField(verbose_name="Pontos Adquiridos em Respostas do Fórum", default = 0)
    badges = models.CharField(verbose_name="Medalhas Adquiridas", default="", max_length=255)
    last_badge_conquered = models.IntegerField(verbose_name="Última Medalha e Status", default=0)
    alerts = models.TextField(verbose_name="Alertas", default="", blank=True)
    
    INTEREST_IRON = 20
    INTEREST_STEEL = 1
    INTEREST_BRONZE = 2
    INTEREST_SILVER = 3
    INTEREST_GOLD = 4
    
    PARTICIPATION_IRON = 5
    PARTICIPATION_STEEL = 6
    PARTICIPATION_BRONZE = 7
    PARTICIPATION_SILVER = 8
    PARTICIPATION_GOLD = 9
    
    COLAB_IRON = 10
    COLAB_STEEL = 11
    COLAB_BRONZE = 12
    COLAB_SILVER = 13
    COLAB_GOLD = 14

    CREATIVE_IRON = 15
    CREATIVE_STEEL = 16
    CREATIVE_BRONZE = 17
    CREATIVE_SILVER = 18
    CREATIVE_GOLD = 19
    
    BADGE_TYPES = (
        (INTEREST_IRON, "Interesse Iron", "/static/images/iron_badge.png"),
        (INTEREST_STEEL, "Interesse Steel", "/static/images/steel_badge.png"),
        (INTEREST_BRONZE, "Interesse Bronze", "/static/images/bronze_badge.png"),
        (INTEREST_SILVER, "Interesse Silver", "/static/images/silver_badge.png"),
        (INTEREST_GOLD, "Interesse Gold", "/static/images/gold_badge.png"),
        
        (PARTICIPATION_IRON, "Participação Iron", "/static/images/iron_badge.png"),
        (PARTICIPATION_STEEL, "Participação Steel", "/static/images/steel_badge.png"),
        (PARTICIPATION_BRONZE, "Participação Bronze", "/static/images/bronze_badge.png"),
        (PARTICIPATION_SILVER, "Participação Silver", "/static/images/silver_badge.png"),
        (PARTICIPATION_GOLD, "Participação Gold", "/static/images/gold_badge.png"),
        
        (COLAB_IRON, "Colaboração Iron", "/static/images/iron_badge.png"),
        (COLAB_STEEL, "Colaboração Steel", "/static/images/steel_badge.png"),
        (COLAB_BRONZE, "Colaboração Bronze", "/static/images/bronze_badge.png"),
        (COLAB_SILVER, "Colaboração Silver", "/static/images/silver_badge.png"),
        (COLAB_GOLD, "Colaboração Gold", "/static/images/gold_badge.png"),
        
        (CREATIVE_IRON, "Criatividade Iron", "/static/images/iron_badge.png"),
        (CREATIVE_STEEL, "Criatividade Steel", "/static/images/steel_badge.png"),
        (CREATIVE_BRONZE, "Criatividade Bronze", "/static/images/bronze_badge.png"),
        (CREATIVE_SILVER, "Criatividade Silver", "/static/images/silver_badge.png"),
        (CREATIVE_GOLD, "Criatividade Gold", "/static/images/gold_badge.png")
    )

    @classmethod
    def get_badge_name(cls, badge_id):
        badges = [c[1] for c in Profile.BADGE_TYPES if c[0] == badge_id]
        if badges:
            return badges[0]
        return None
    
    @classmethod
    def get_badge_tuples_by_name(cls, badge_name):
        badges = [c for c in Profile.BADGE_TYPES if badge_name.lower() in c[1].lower()]
        
        return badges
        
    
    def get_badges_by_type(self, type):
        tuples = Profile.get_badge_tuples_by_name(type)
        filtered_badges = [t for t in tuples if t[1] in self.badges]
        
        return filtered_badges

    def decrement_reply_point(self):
        self.reply_points -= 1
        badges = self.verify_badge_achievement()
        self.badges = ";".join(badges)
        self.save()
    
    def decrement_comment_point(self):
        self.comment_points -= 1
        badges = self.verify_badge_achievement()
        self.badges = ";".join(badges)
        self.save()

    

    def has_unotified_badge(self):
        return self.last_badge_conquered > 0
    
    def get_and_notify_badge(self):
        badge = self.last_badge_conquered
        if badge:
            self.last_badge_conquered = 0
            self.save()
            classrooms = self.user.classrooms.all()
            for classroom in classrooms:
                message_to_teachers = f'[AprendaFazendo] {self.user.first_name} ganhou uma nova medalha!'
                [send_mail(message_to_teachers, '', '', [teacher.email], html_message=message_to_teachers) for teacher in classroom.teachers.all()]

        
        return badge
    
    def register_action(self, action):
        current_date_time = timezone.localtime().strftime("%d/%m/%Y às %H:%M:%S")
        if not self.actions_log:
            self.actions_log = ""
        self.actions_log += f"\n {action} em {current_date_time};"
        self.update_user_points(action)
        badges = self.verify_badge_achievement()
        registered_badges = self.badges.split(";")
        self.badges = ";".join(badges)
        new_badges = [b for b in badges if not b in registered_badges]
        if new_badges:
            newest_badge = new_badges[0]
            self.last_badge_conquered = Profile.get_badge_tuples_by_name(newest_badge)[0][0]
            self.save()
            return self.last_badge_conquered
        
        self.save()
        return None
    
    def list_actions(self):
        if self.actions_log:
            return self.actions_log.split("\n")
        return []
    
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:profile_detail', [self.user.id]

    def update_user_points(self, action):
        if "comentário" in action:
            self.comment_points += 1
        if "Respondendo ao Post" in action:
            self.reply_points += 1
        if "Resposta" in action and "enviada com sucesso" in action:
            self.answer_points += 1
        if "Criando postagem" in action or "Nova versão" in action:
            self.post_points += 1

    def verify_badge_achievement(self):
        badge = None
        badges_achieved = []

        if self.answer_points >= 2:
            badge = self.INTEREST_IRON
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.answer_points >= 5:
            badge = self.INTEREST_STEEL
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.answer_points >= 9:
            badge = self.INTEREST_BRONZE
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.answer_points >= 15:
            badge = self.INTEREST_SILVER
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.answer_points >= 25:
            badge = self.INTEREST_GOLD
            badges_achieved.append(Profile.get_badge_name(badge))
        
        if self.comment_points >= 2:
            badge = self.PARTICIPATION_IRON
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.comment_points >= 5:
            badge = self.PARTICIPATION_STEEL
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.comment_points >= 9:
            badge = self.PARTICIPATION_BRONZE
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.comment_points >= 15:
            badge = self.PARTICIPATION_SILVER
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.comment_points >= 25:
            badge = self.PARTICIPATION_GOLD
            badges_achieved.append(Profile.get_badge_name(badge))

        if self.reply_points >= 1:
            badge = self.COLAB_IRON
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.reply_points >= 3:
            badge = self.COLAB_STEEL
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.reply_points >= 5:
            badge = self.COLAB_BRONZE
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.reply_points >= 10:
            badge = self.COLAB_SILVER
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.reply_points >= 15:
            badge = self.COLAB_GOLD
            badges_achieved.append(Profile.get_badge_name(badge))
        
        if self.post_points >= 1:
            badge = self.CREATIVE_IRON
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.post_points >= 3:
            badge = self.CREATIVE_STEEL
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.post_points >= 5:
            
            badge = self.CREATIVE_BRONZE
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.post_points >= 10:
            badge = self.CREATIVE_SILVER
            badges_achieved.append(Profile.get_badge_name(badge))
        if self.post_points >= 15:
            badge = self.CREATIVE_GOLD
            badges_achieved.append(Profile.get_badge_name(badge))
        
        return badges_achieved
        
        

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, actions_log="Criado em %s"%timezone.localtime().strftime("%d/%m/%Y às %H:%M:%S"))
        

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
    enabled = models.BooleanField(default=True, verbose_name="Habilitado?")
    class Meta:
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return u"%s" % self.name
        
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:discipline_detail', [self.uuid]

class GradingStrategy(object):
    
    #TODO reimplement punishimnent for copies. Not working in this version
    
    def calculate_avg(self, questions, students, test=None):
        query_params = {}
        
        if isinstance(questions, QuerySet):
            questions_count = questions.count()
        else:
            questions_count = len(questions)

        if test:
            query_params["test"] = test
        
        team_questions = [q for q in questions if q.is_team_work]

        individual_questions = [q for q in questions if not q.is_team_work]
        grades_sum_per_student = dict((s.id, [s, 0.0]) for s in students)
        if team_questions:
            teams = [t for s in students for t in s.teams.all() ]
            query_params["team__in"] = teams
            query_params["question__in"] = team_questions
            team_answers = Answer.objects.filter(**query_params).values("team__members__id").annotate(grade_sum=Sum('grade')*10)
            for a in team_answers:
                grades_sum_per_student[a['team__members__id']][1] = a['grade_sum']/questions_count
        
        if individual_questions:
            query_params["question__in"] = individual_questions
            query_params["student__in"] = students
            individual_answers = Answer.objects.filter(**query_params).values("student").annotate(grade_sum=Sum('grade')*10)
            for a in individual_answers:
                grades_sum_per_student[a['student']][1] = a['grade_sum']/questions_count

        return list(grades_sum_per_student.values())

    def calculate_wavg(self, questions, students, test=None):
        query_params = {}
        questions_weight_sum = sum([q.weight for q in questions])
        if test:
            query_params["test"] = test

        team_questions = [q for q in questions if q.is_team_work]
        individual_questions = [q for q in questions if not q.is_team_work]
        grades_sum_per_student = dict((s.id, [s, 0.0]) for s in students)
        if team_questions:
            teams = [t for s in students for t in s.teams.all() ]
            query_params["team__in"] = teams
            query_params["question__in"] = team_questions
            team_answers = Answer.objects.filter(**query_params).values("team__members__id").annotate(grade_sum=Sum(F('grade') * F('question__weight')))
            for a in team_answers:
                grades_sum_per_student[a['team__members__id']][1] = float("%.1f" % ((a['grade_sum']/questions_weight_sum) * 10))

        if individual_questions:
            query_params["question__in"] = individual_questions
            query_params["student__in"] = students
            individual_answers = Answer.objects.filter(**query_params).values("student").annotate(grade_sum=Sum(F('grade') * F('question__weight')))
            for a in individual_answers:
                grades_sum_per_student[a['student']][1] = float("%.1f" % ((a['grade_sum']/questions_weight_sum) * 10))

        return list(grades_sum_per_student.values())


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
    
    def get_deadlines(self, classrooms=[]):
        if classrooms:
            deadlines = self.deadlines.filter(classroom__in= classrooms).all()
            return deadlines
        
        deadlines = self.deadlines.all()
        return deadlines
        
        
    def text_escaped(self):
        return u'%s' % html.unescape(strip_tags(self.topic_content))
    
    def get_latest_approved_version(self):
        if not self.versions.exists():
            first_version = self.versions.create(content=self.topic_content, approved=True, user=self.owner, topic=self)
            return first_version
        
        return self.versions.filter(approved=True).order_by("-id").first()
    
    def sorted_versions(self):
        return self.versions.order_by("-id")

    def has_completed(self, student):
        questions_count = self.question_set.count()
        answers_count = Answer.objects.filter(student = student, question__in = self.question_set.all()).count()
        has_sent_answers_to_all_questions =  answers_count >= questions_count
        return has_sent_answers_to_all_questions


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

    def is_closed_for(self, student):
        classrooms = Classroom.objects.filter(students__id = student.id)
        for klass in classrooms:
            closed_topics = klass.closed_topics.all()
            return self in closed_topics
        return False


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
        return grader.calculate_avg(self.question_set.all(), classroom.students.all())
    
    def calculate_grades_wavg(self, classroom):
        grader = GradingStrategy()
        return grader.calculate_wavg(self.question_set.all(), classroom.students.all())
    
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

class ForumPost(models.Model, AdminURLMixin):
    
    topic = models.ForeignKey(Topic, verbose_name="Postagem em Fórum", on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.TextField(verbose_name="Título", unique=True)
    content = RichTextUploadingField(verbose_name="Conteúdo")
    publish_date = models.DateField(auto_now=True)
    

    def __str__(self):
        return u"%s"%self.title
    
    @models.permalink
    def get_absolute_url(self):
        return "mydidata:post_detail", (self.id,)

    

class Reply(models.Model, AdminURLMixin):
    to_post = models.ForeignKey(ForumPost, verbose_name="Resposta", on_delete=models.CASCADE, related_name="replies")
    publish_date = models.DateField(auto_now=True)
    content = RichTextUploadingField(null=True, blank=True, verbose_name="Resposta")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")

    def __str__(self):
        creator_str = f"{self.author.first_name}({self.author.username})"
        return u"Resposta de '%s' por %s"%(self.to_post.title, creator_str)

class Test(models.Model, AdminURLMixin):
    uuid = ShortUUIDField(unique=True)
    title = models.CharField(max_length=200, default="test", verbose_name="Título")
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, verbose_name="Tópico", related_name="tests")
    limit_per_try = models.IntegerField(default=5)
    max_tries = models.IntegerField(default=2, verbose_name="Tentativas")
    key = models.CharField(max_length=200, default="testkey", verbose_name="Frase de Envio")
    class Meta:
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return u"%s" % self.title

    
    def has_participant(self, student_id):
        has_test_user_relation = [t for t in self.test_user_relations.all() if t.student.id == student_id]
        if has_test_user_relation:
            return True
        return False


    def is_closed(self, classroom):
        return classroom in self.closed_for_classrooms.all()

    def is_closed_for(self, user):

        test_user = TestUserRelation.objects.filter(test=self, student=user).first()
        classrooms = Classroom.objects.filter(students__id = user.id)
        for klass in classrooms:
            if self.is_closed(klass):
                return True
        
        return (test_user and test_user.is_closed)
    
    def has_weigthed_questions(self):
        return [q for q in self.questions.all() if q.weight != 1.0]

    def get_answers(self, student):
        return Answer.objects.filter(student=student, question__id__in=self.get_ordered_questions(), test=self)

    def close_for(self, student):
        test_user = self.get_or_create_test_user_relation(student)
        test_user.is_closed = True
        test_user.save()

    def close(self, classroom):
        self.closed_for_classrooms.add(classroom)
        [t.close() for t in self.test_user_relations.all()]
        self.save()
    
    def open(self, classroom):
        self.closed_for_classrooms.remove(classroom)
        [t.open() for t in self.test_user_relations.all()]
        self.save()



    def get_or_create_test_user_relation(self, user):
        test_user = TestUserRelation.objects.filter(student=user, test=self).first()
        if not test_user:
            test_user = TestUserRelation.objects.create(student=user, test=self)
        return test_user
    
    def has_next_try(self, user):
        return self.get_or_create_test_user_relation(user).tries < self.max_tries
    
    
    def next_try(self, student):
        if not self.has_next_try(student):
            raise Exception("Amount of tries exceeded the limit: %s"%self.max_tries)

        test_user_rel = self.get_or_create_test_user_relation(student)
        self.get_answers(student).delete()
        test_user_rel.tries += 1
        test_user_rel.generate_question_index()

        test_user_rel.save()

        return test_user_rel.current_questions()
    
    def next_question(self, user, question):
        if self.is_closed_for(user):
            return None
        tu = self.get_or_create_test_user_relation(user)
        return tu.get_next_question(question)
        
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
    
    def calculate_grades(self, classroom=None, students = []):
        grader = GradingStrategy()
        grades_by_student = {}
        
        if not students and classroom:
            students = classroom.students.all().prefetch_related("test_relations").order_by('first_name')
        grader_function = grader.calculate_avg
        if self.has_weigthed_questions():
            grader_function = grader.calculate_wavg
        grades = grader_function(self.questions.all(), students, self)
        
        for g in grades:
            student, grade = g
            if not grades_by_student.get(student, None):
                grades_by_student[student] = { }
            
            test_user_rels = [test_user for test_user in student.test_relations.all() if test_user.test == self]
            
            if not test_user_rels:
                grades_by_student[student]['grade'] = "?"
                continue
            
            test_user_rel = test_user_rels[0]
            grades_by_student[student]['grade'] = grade
            grades_by_student[student]['test_user'] = test_user_rel
            if self.has_next_try(student):
                grades_by_student[student]['next_try_link'] = reverse('mydidata:next_try', args=(test_user_rel.id,))
        
        return grades_by_student
    
    def calculate_grades_for_student(self, student):
        
        return self.calculate_grades(students=[student])
    


class Classroom(models.Model):
    uuid = ShortUUIDField(unique=True)
    academic_site_id = models.IntegerField(verbose_name = "Identificador no Acadêmico", default=0)
    name = models.CharField(max_length=255, verbose_name="Nome")
    students = models.ManyToManyField(User, null=True, blank=True, verbose_name="Estudantes", related_name="classrooms")
    disciplines = models.ManyToManyField(Discipline, null=True, verbose_name="Disciplinas", related_name="classrooms")
    closed_topics = models.ManyToManyField(Topic, null=True, blank=True, verbose_name="Tópicos Fechados")
    closed_tests = models.ManyToManyField(Test, null=True, blank=True, related_name="closed_for_classrooms", verbose_name="Avaliações Fechadas")
    tests = models.ManyToManyField(Test, null=True, blank=True, verbose_name="Avaliações", related_name="classrooms")
    teachers = models.ManyToManyField(User, verbose_name = "Professores")

    class Meta:
        verbose_name_plural = 'Turmas'
    
    @models.permalink
    def get_absolute_url(self):
        return 'mydidata:class_detail', [self.id]
    
    @models.permalink
    def get_progress_url(self):
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
    question_text = RichTextUploadingField(verbose_name='Enunciado da Questão')
    ref_keywords = models.TextField(verbose_name="Palavras-Chave para Feedback Automático", blank=True)
    file_types_accepted = models.CharField(max_length=255, verbose_name="Tipos de arquivos aceitos", null=True, blank="True")
    text_required = models.BooleanField(default=False, verbose_name='Resposta de texto obrigatória?')
    weight = models.FloatField(default=1.0,  verbose_name='Peso')
    file_upload_only = models.BooleanField(default=False, verbose_name="Aceitar somente upload de arquivos?")
    punish_copies = models.BooleanField(default=False,verbose_name="punir cópias exatas?")
    punishment_percent = models.PositiveSmallIntegerField(default=30, verbose_name="Percentual da Punição")
    test_inputs = models.CharField(null=True, blank=True, max_length=255, verbose_name = "entrada separa por vírgulas")
    expected_output = models.CharField(null=True, blank=True, max_length=255, verbose_name = "saída esperada do programa (ou parte)")
    is_team_work = models.BooleanField(default=False, verbose_name="Somente equipes podem responder?")
    should_block_paste = models.BooleanField(default=True, verbose_name="Deseja impedir ações de copiar e colar nas respostas?")

    DIFFICULTY_LIST = (
        (1, 'Difícil'),
        (2, 'Médio'),
        (3, 'Fácil'),
    )
    difficulty_level = models.PositiveSmallIntegerField(choices=DIFFICULTY_LIST, verbose_name="Dificuldade", default=2)
    TYPE_LIST = (
        (1, "Exercício"),
        (2, "Trabalho"),
        (3, "Prova")
    )
    question_type = models.PositiveSmallIntegerField(choices=TYPE_LIST, verbose_name="Tipo", default=1)
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
        return len(self.choices.all()) == 0 and not self.is_c_programming()

    def is_c_programming(self):
        return self.expected_output
    
    def is_multiple_choice(self):
        return len(self.choices.all()) > 0
    
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
        if next_index < len(ordered_questions):
            return ordered_questions[next_index]
        return None
        
        
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
        if self.is_discursive():
            return 'mydidata:discursive_question_edit', [self.uuid]
        if self.test_inputs:
            return 'mydidata:c_programming_question_edit', [self.uuid]
        return 'mydidata:multiple_choice_question_edit', [self.uuid]
        

    @models.permalink
    def get_delete_url(self):
        return 'mydidata:question_delete', [self.id]
    
    @models.permalink
    def get_answer_url_for_test(self, test):
        return 'mydidata:test_answer', (self.uuid, test.id)

    @models.permalink
    def get_answer_url(self):
        
        if self.is_discursive() or self.is_c_programming():
            return 'mydidata:discursive_answer', [self.uuid]
        else:
            return 'mydidata:multiple_choice_answer', [self.uuid]

    
    @models.permalink
    def get_test_url(self):
        return 'mydidata:test_for', [self.uuid]

    def shuffled_choice_set(self):
        choice_list = list(self.choices.all())
        random.shuffle(choice_list)
        return choice_list

      
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Questão", related_name="choices")
    # choice_text = RichTextUploadingField(verbose_name='Texto da Alternativa')
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False, verbose_name="É a alternativa correta?")
    class Meta:
        verbose_name_plural = 'Alternativas'
        
    def __str__(self):
        return self.choice_text

class Team(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Líder", related_name="owner_of")
    members = models.ManyToManyField(User, related_name='teams')

    @models.permalink
    def get_absolute_url(self):
        return "mydidata:team_detail", [self.id]
    @models.permalink
    def get_edit_url(self):
        return "mydidata:edit_team", [self.id]
    def __str__(self):
        return self.name


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
        (ALMOST_CORRECT, 'Quase Perfeita (0.6 - 0.8)'),
        (ACCEPTABLE, 'Aceitável (0.3 - 0.6)'),
        (ALMOST_INCORRECT, 'Apresenta muitos erros (0.1 - 0.3)'),
        (INCORRECT, 'Errada (0.0)'),
    ]

    answer_text = RichTextUploadingField(null=True, blank=True, verbose_name="Texto")
    assignment_file = models.FileField(upload_to='assignments/%Y/%m/%d', null=True, blank=True, storage=PublicMediaStorage(), verbose_name="Arquivo")
    feedback = models.TextField(null=True, blank=True, verbose_name="Correções")
    status = models.IntegerField(choices=(STATUS_CHOICES + EVAL_CHOICES), default=SENT, verbose_name="Avaliação")
    grade = models.FloatField(default=0.0, verbose_name="Nota")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Questão", related_name="answers")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudante")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Equipe", related_name='answers', null=True, blank=True)
    test = models.ForeignKey(Test, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Avaliação", related_name="answers")
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="Alternativa")
    graphic_annotations = models.TextField(blank=True)
    
    

    class Meta:
        verbose_name_plural = 'Respostas'
    
    def is_graphic_answer(self):
        return self.assignment_file and self.assignment_file.url.lower().split(".")[-1] in ["jpg", "png", "jpeg", "pdf", "tiff", "psd"]
    
    @classmethod
    def find(cls, student, question, test=None):
        args = {'student': student, 'question': question}
        if test:
            args['test'] = test
        return cls.objects.filter(**args).first()

    def graphic_annotations_unscaped(self):
        return html.unescape(self.graphic_annotations)
    
    def is_automatic_verification_enabled(self):
        return self.id and self.answer_text and self.question.ref_keywords or self.question.expected_output
    
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
        correct_choice = self.question.choices.filter(is_correct=True).first()
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
            if expected not in str(output):
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
        if self.question.is_multiple_choice():
            return "mydidata:multiple_choice_answer_detail", [self.id]
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
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_relations")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_user_relations")
    index_list = models.CharField(max_length=255, verbose_name=_("índices"),)
    is_closed = models.BooleanField(default=False)
    tries = models.IntegerField(default=1)
    key = models.CharField(max_length=255, verbose_name=_("Chave de Envio"), default="stub_key")
    class Meta:
        verbose_name_plural = 'Índices de Questões'
    
    def __str__(self):
        return str(self.student.first_name + " " + self.student.last_name + ": " + self.test.title)
    
    def save(self, *args, **kwargs):
        if not self.index_list:
            self.generate_question_index()
        return super(TestUserRelation, self).save(*args, **kwargs)

    def index_list_as_array(self):
        return eval(self.index_list)

    def generate_question_index(self):
        import random
        
        questions = list(self.test.questions.order_by('uuid').all())
        next_index_list = self.index_list

        while next_index_list == self.index_list:
            
            index_list = [questions.index(q)+1 for q in questions]
            str(random.shuffle(index_list))
            next_index_list = str(index_list)
            
        self.index_list = next_index_list
        return self.index_list
    
    def current_questions(self):
        index_array = self.index_list_as_array()
        return [list(self.test.questions.order_by('uuid'))[i-1] for i in index_array ]

    def current_non_answered_questions(self):
        index_array = self.index_list_as_array()
        current_questions = [list(self.test.questions.prefetch_related("answers").order_by('uuid'))[i-1] for i in index_array ]
        non_answerd_questions = list(self.test.questions.exclude(answers__test= self.test, answers__student = self.student).all())

        non_answerd_questions.sort(key=lambda q: current_questions.index(q))
        return non_answerd_questions
    
    def remaining_tries(self):
        return self.test.max_tries - self.tries
    
    def has_next_try(self):
        return self.test.has_next_try(self.student)
    
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
    
    #TODO refactor
    def get_next_question(self, question):
        questions = self.current_questions()
        non_answerd_questions = self.current_non_answered_questions()
        self_index = questions.index(question)
        next_index = self_index + 1
        while next_index < len(questions) and questions[next_index] not in non_answerd_questions:
            next_index += 1
        
        if next_index < len(questions):
            return questions[next_index]

        return None
    
    def get_next_answer_url(self, question):
        nextQuestion = self.get_next_question(question)

        if nextQuestion:
            return reverse("mydidata:test_answer", args=(nextQuestion.uuid, self.test.id,))
        
        return ""
    
    def close(self):
        self.is_closed = True
        self.save()
    
    def open(self):
        self.is_closed = False
        self.save()
        
        

class Deadline(models.Model, AdminURLMixin):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, verbose_name="Tópico", related_name="deadlines")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="deadlines")
    due_datetime = models.DateTimeField()
    
    def __str__(self):
        return "%s para %s vence em %s"%(self.topic.topic_title, self.classroom.name, self.get_local_due_date())

    def get_local_due_date(self):
        return timezone.localtime(self.due_datetime).strftime("%d/%m/%Y às %H:%M:%S")

    def datetime_to_str(self):
        formatedDate = self.due_datetime.strftime("%d/%m/%Y às %H:%M:%S")
        return formatedDate
    
    def get_remaining_time(self):
        time_remaining = self.due_datetime - timezone.now()
        # time_remaining_str = str(time_remaining)
        days_remaining = time_remaining.days
        if time_remaining.total_seconds() > 0:
            days_remaining = time_remaining.days
            hours_remaining = int(time_remaining.seconds / 3600)
            minutes_remaining = int((time_remaining.seconds % 3600) / 60)
            seconds_remaining = int(time_remaining.seconds % 60)
        else:
            days_remaining = 0
            hours_remaining = 0
            minutes_remaining = 0
            seconds_remaining = 0
        
        time_remaining_str = f"{days_remaining}d {hours_remaining}h {minutes_remaining}m {seconds_remaining}s"
        
        
        return time_remaining_str


class Comment(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = RichTextUploadingField(null=True, blank=True, verbose_name="Texto")
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "%s: %s - %s..."%(self.author.first_name, self.topic.topic_title, self.body[:20])