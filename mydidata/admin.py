from django.contrib import admin

from django import forms
from django.contrib import admin
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.utils.html import format_html
from .models import Question, Discipline
from .models import Comment, ContentVersion, Choice, Topic, Test, Answer, Classroom, ResourceRoom, TestUserRelation, Deadline, Team, Profile
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.forms import inlineformset_factory

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionInline(admin.StackedInline):
    model = Question
    question_text = forms.CharField(widget=CKEditorUploadingWidget())
    filter_horizontal = ('tests',)
    question_text.label = "Texto"
    readonly_fields = ('question_link',) 
    def question_link(self, obj):
        question_url = "/admin/mydidata/question/"+str(obj.id)+"/change/"
        return mark_safe('<a href="%s">%s</a>' % (question_url, "visualizar"))
    question_link.allow_tags = True
    extra = 1
    
class TopicInline(admin.TabularInline):
    model = Topic
    exclude = ('topic_content',)
    readonly_fields = ('edit_link', )
    def edit_link(self, obj):
        return mark_safe('<a href="%s">%s</a>'%(obj.get_admin_url(), obj.topic_title))
    edit_link.allow_tags = True
    extra = 1
    ordering = ('order',)

class QuestionAdminForm(forms.ModelForm):
    question_text = forms.CharField(widget=CKEditorUploadingWidget())
    question_text.label = "Texto"

    class Meta:
        model = Question
        fields = '__all__'

class TeamAdmin(admin.ModelAdmin):
    model = Team
    filter_horizontal = ('members',)

class ClassroomAdmin(admin.ModelAdmin):
    model = Classroom
    filter_horizontal = ('students', 'disciplines', 'closed_topics', 'tests', 'closed_tests')
    def save_model(self, request, obj, form, change):        
        import random
        obj.save()
        if obj.tests:
            for test in obj.tests.all():
                for student in obj.students.all():
                    tu = TestUserRelation.objects.filter(student=student, test=test)
                    if not tu:
                        tu = TestUserRelation.objects.create(student=student, test=test)
                        tu.generate_question_index()
                        tu.save()   
        

class ResourceRoomAdmin(admin.ModelAdmin):
    model = ResourceRoom
    filter_horizontal = ('students', 'topics',)

class DisciplineAdmin(admin.ModelAdmin):
    model = Discipline
    inlines = [
        TopicInline,
    ]

def get_formated_text(self):
    return format_html(u'%s ...' % self.question_text[0:200])
    
    
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    filter_horizontal = ('tests',)
    search_fields = ['question_text']

    list_filter = ('tests',)
    inlines = [
        ChoiceInline,
        AnswerInline,
    ]

class TopicAdminForm(forms.ModelForm):
    topic_content = forms.CharField(widget=CKEditorUploadingWidget())
    topic_content.label = "Conteúdo"
    class Meta:
        model = Topic
        fields = '__all__'

class TopicAdmin(admin.ModelAdmin):
    form = TopicAdminForm
    show_change_link = True
    inlines = [
        QuestionInline,
    ]

class TestAdminForm(forms.ModelForm):
  classrooms_closed = forms.ModelMultipleChoiceField(
    queryset=Classroom.objects.all(), 
    required=False,
    widget=FilteredSelectMultiple(
      verbose_name='Turmas',
      is_stacked=False
    )
  )

  classrooms = forms.ModelMultipleChoiceField(
    queryset=Classroom.objects.all(), 
    required=False,
    widget=FilteredSelectMultiple(
      verbose_name='Turmas',
      is_stacked=False
    )
  )


  class Meta:
    model = Test
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(TestAdminForm, self).__init__(*args, **kwargs)

    if self.instance and self.instance.pk:
      self.fields['classrooms_closed'].initial = self.instance.closed_for_classrooms.all()
      self.fields['classrooms_closed'].label = "Fechado para Turmas"
      self.fields['classrooms'].initial = self.instance.classrooms.all()
      self.fields['classrooms'].label = "Turmas"
      self.fields['title'].label = "Título"
      self.fields['topic'].label = "Tópico"
      

  def save(self, commit=True):
    test = super(TestAdminForm, self).save(commit=False)

    if commit:
      test.save()

    if test.pk:
        test.classrooms.set(self.cleaned_data['classrooms'])
        test.closed_for_classrooms.set(self.cleaned_data['classrooms_closed'])
        self.save_m2m()
        for croom in self.cleaned_data['classrooms']:
            for student in croom.students.all():
                tu = TestUserRelation.objects.filter(student=student, test=test).first()
                if not tu:
                    tu = TestUserRelation.objects.create(student=student, test=test)
                tu.generate_question_index()
                tu.save()
    return test

class TestQuestionInline(admin.TabularInline):
    model = Test.questions.through
    question_text = forms.CharField(widget=CKEditorUploadingWidget())
    
    question_text.label = "Texto"
    readonly_fields = ('question_link',) 
    def question_link(self, obj):
        question_url = "/admin/mydidata/question/"+str(obj.question.id)+"/change/"
        return mark_safe('<a href="%s">%s</a>' % (question_url, "visualizar"))
    question_link.allow_tags = True
    extra = 1

class TestAdmin(admin.ModelAdmin):
    form = TestAdminForm
    show_change_link = True
    
    inlines = [
        TestQuestionInline,
    ]
    exclude = ('questions',)
   
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Answer)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Classroom, ClassroomAdmin)
admin.site.register(ResourceRoom, ResourceRoomAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(TestUserRelation)
admin.site.register(Deadline)
admin.site.register(ContentVersion)
admin.site.register(Team, TeamAdmin)
admin.site.register(Comment)
admin.site.register(Profile)



# Register your models here.

