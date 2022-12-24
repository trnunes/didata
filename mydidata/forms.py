# -*- coding: utf-8 -*-
from random import choices
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm
from .models import ContentVersion, Topic, Question, Profile, Choice, Discipline, Classroom, Answer, TestUserRelation
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import modelform_factory
from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('student_id',)

class SubscriberForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'email', 'username',)
    first_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={'class':'form-control'})
    )
    email = forms.EmailField(
        required=True, widget=forms.TextInput(attrs={'class':'form-control'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control', 'type':'password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['password2']
    # disciplines = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple)
    # def __init__(self,*args,**kwargs):
    #     print kwargs
    #     self.classroom = kwargs.pop('classroom')
    #     super(SubscriberForm,self).__init__(*args,**kwargs)
    #     self.fields['disciplines'] = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple, choices=self.classroom.disciplines.all().values_list('id', 'name'))

class UserUpdateForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        del self.fields['password']
    
    
    class Meta:
        model = User
        fields=["first_name", "username", "email",]
    
    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        if self.instance.username == username:
            return username
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            "Já existe um usuário com esse nome de usuário.",
            code='duplicate_username',
        )

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('topic_title', 'label','topic_content', 'order', 'owner')
        widgets = {
            'topic_title': forms.TextInput(
                attrs={
                    'placeholder':'Title',
                    'class':'col-md-12 form-control'
                }
            ),
            'topic_content': forms.CharField(widget=CKEditorUploadingWidget(), label="Conteúdo", required=False),

            'order': forms.TextInput(
                attrs={
                    'placeholder':'Ordem',
                    'class':'gi-form-addr form-control'
                }
            ),
            
        }
    def __init__(self, *args, **kwargs):
        if kwargs.get("owner", None):
            self.owner = kwargs.pop("owner")
        super(TopicForm, self).__init__(*args, **kwargs)
        # self.fields['owner'] =  forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=User.objects.all(), label="Selecione o dono do tópico", empty_label=None, )

    def save(self, *args, **kwargs):
        instance = super(TopicForm, self).save(*args, **kwargs)
        if not instance.versions.exists():
            first_version = instance.versions.create(content=instance.topic_content, approved=True, topic=instance, user = instance.owner)
        return instance

    
class ContentVersionForm(forms.ModelForm):
    class Meta:
        model = ContentVersion
        fields = ('content',)
        widgets = {
            'content': forms.CharField(widget=CKEditorUploadingWidget, label='Conteúdo')

        }

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop("user")
        if 'topic' in kwargs:
            self.topic = kwargs.pop('topic')
        if 'instance' in kwargs:
            self.topic = kwargs.get('instance').topic
        
        super(ContentVersionForm, self).__init__(*args, **kwargs)

        if not 'instance' in kwargs:
            self.fields['content'].initial = self.topic.topic_content
    
    def save(self, *args, **kwargs):
        if not self.user:
            raise("Not able to save a content version without a user")
        if not self.topic:
            raise("Not able to save a content version without a topic")
        
        instance =  super(ContentVersionForm, self).save(*args, **kwargs, commit=False)
        instance.user = self.user
        instance.topic = self.topic
        instance.save()
        return instance





        
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question_text', 'difficulty_level', 'question_type', 'topic',)
        widgets = {
            'question_text': forms.Textarea(
                attrs={'placeholder':'Enunciado', 'class':'col-md-12 form-control'}
            ),
            'difficulty_level': forms.Select(
                attrs={'placeholder':'Dificuldade', 'class':'form-control'}
            ),
            'question_type': forms.Select(
                attrs={'placeholder':'Tipo', 'class':'form-control'}
            ),
        }

class AnswerFormUploadOnly(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ['assignment_file',]

        labels = {
            'assignment_file': 'Arquivo da Resposta',
        }
    def clean_assignment_file(self):

        file = self.cleaned_data.get("assignment_file")
        question = self.instance.question
        if not file and not question.file_types_accepted:
            return file

        if not file and question.file_types_accepted:
            raise ValidationError(_("Você deve enviar um arquivo como anexo a esta questão! Clique no botão \"Escolher Arquivo\" e depois envie a resposta."))

        file_type = file.name.split(".")[-1]
        if question.file_types_accepted and not file_type in question.file_types_accepted and not "todos" in question.file_types_accepted:
            raise ValidationError(_("Arquivo de resposta inválido para esta questão. Apenas os tipos %(tipos)s são aceitos!"), 
                params = {'tipos': str(question.file_types_accepted)},
            )        
        return file

class AnswerForm(forms.ModelForm):
    # choice = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=Choice.objects, label="Selecione a sua resposta", empty_label=None)

    class Meta:
        model = Answer
        fields = ('assignment_file','answer_text', 'choice',)

        widgets = {
            'answer_text' : forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
            # 'choice': forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=Choice.objects.none(), label="Selecione a sua resposta", empty_label=None)
        }
        labels = {
            'answer_text': 'Digite sua Resposta Aqui',
            'assignment_file': 'Arquivo da Resposta',            
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        question = kwargs.pop('question', None)
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        # self.fields['choice'] = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=question.choice_set, label="Selecione a sua resposta", empty_label=None)
        if question and question.is_discursive():
            self.fields.pop('choice', None)
        
        if question and question.file_upload_only:
            self.fields.pop('answer_text', None)

        if question and not question.is_discursive():
            self.fields.pop('answer_text', None)
            self.fields['choice'] = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=question.choice_set, label="Selecione a sua resposta", empty_label=None)
            self.fields.pop('assignment_file', None)
            

    # def clean_choice(self):
    #     question = self.instance.question
    #     choice = question.choice_set.get(pk=self.cleaned_data['choice'])
    #     print("Selected choice: ", choice.choice_text)
    #     if not choice:
    #         raise ValidationError(_("A resposta selecionada não existe mais!"))
        
    #     return choice

    def clean_assignment_file(self):

        file = self.cleaned_data.get("assignment_file")
        question = self.instance.question
        if not file and not question.file_types_accepted:
            return file

        if not file and question.file_types_accepted:
            raise ValidationError(_("Você deve enviar um arquivo como anexo a esta questão! Clique no botão \"Escolher Arquivo\" e depois envie a resposta."))

        file_type = file.name.split(".")[-1]
        if question.file_types_accepted and not file_type in question.file_types_accepted and not "todos" in question.file_types_accepted:
            raise ValidationError(_("Arquivo de resposta inválido para esta questão. Apenas os tipos %(tipos)s são aceitos!"), 
                params = {'tipos': str(question.file_types_accepted)},
            )        
        return file
    
    def clean_answer_text(self):
        student = self.instance.student
        classrooms = Classroom.objects.filter(students__id = student.id).all()
        question = self.instance.question
        topic = question.topic
        test = self.instance.test
        c_list = [classroom for classroom in classrooms if topic in classroom.closed_topics.all()]
        t_classes = []
        if test:
            t_classes = [classroom for classroom in classrooms if test in classroom.closed_tests.all()]
        tuserrelation = TestUserRelation.objects.filter(test=test,student=student).first()
        closed_for_student = (tuserrelation and tuserrelation.is_closed)
        
        if closed_for_student:
            raise ValidationError(_("Questão fechada para envio de respostas!"))
        text = self.cleaned_data.get("answer_text")
        if question.text_required and not text:
            raise ValidationError(_("Sua resposta não pode ser em branco! Por favor, escreva a sua reposta na caixa de texto abaixo."))
        return text

# class SuperuserAnswerForm(forms.ModelForm):
    # status = forms.MultipleChoiceField(choices=Answer.STATUS_CHOICES, widget=forms.CheckboxSelectMultiple()),
    # class Meta:
        # model = Answer
        # fields = ['answer_text', 'assignment_file']
# 
        # widgets = {
            # 'answer_text': forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
# 
        # }
        # labels = {
            # 'answer_text': 'Resposta Aqui',
        # }
# 
        # fields += ['feedback', 'status', 'grade']
        # 
        # 
        # labels['feedback'] = 'Correções Aqui'
        # 
    # def clean_grade(self):
        # if float(self.cleaned_data.get("status")) == Answer.CORRECT:
            # self.cleaned_data["grade"] = 1.0
# 
            # 
            # 
        # if float(self.cleaned_data.get("status")) == Answer.ALMOST_CORRECT:
            # self.cleaned_data["grade"] = 0.8
        # 
        # if float(self.cleaned_data.get("status")) == Answer.ALMOST_INCORRECT:
            # self.cleaned_data["grade"] = 0.4
        # 
        # if float(self.cleaned_data.get("status")) == Answer.INCORRECT:
            # self.cleaned_data["grade"] = 0.0
        # 
        # return self.cleaned_data["grade"]
# 
    # def is_valid(self):
        # return True

class SuperuserAnswerFormSimplified(forms.ModelForm):
    status = forms.ChoiceField(widget=forms.RadioSelect, choices=Answer.EVAL_CHOICES)
    class Meta:
        model = Answer
        fields = [ "assignment_file", "status", 'feedback', 'grade', ]
        field_order = ["status", "feedback", "grade"]
        labels = {}
        # labels = {
            # 'answer_text': 'Resposta Enviada',
        # }
        # widgets = {
            # 'answer_text': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        # }
        labels['feedback'] = 'Correções Aqui'
    
    # def clean_grade(self):
        # print("Cleaning data: ", float(self.cleaned_data.get("status")) == Answer.ALMOST_CORRECT)
        # if float(self.cleaned_data.get("status")) == Answer.CORRECT:
            # self.cleaned_data["grade"] = 1.0
            # self.ins
            # 
            # 
        # if float(self.cleaned_data.get("status")) == Answer.ALMOST_CORRECT:
            # self.cleaned_data["grade"] = 0.8
        # 
        # if float(self.cleaned_data.get("status")) == Answer.ALMOST_INCORRECT:
            # self.cleaned_data["grade"] = 0.4
        # 
        # if float(self.cleaned_data.get("status")) == Answer.INCORRECT:
            # self.cleaned_data["grade"] = 0.0
        # 
        # return self.cleaned_data["grade"]
                
    # def clean_status(self):
        # print("Cleaning status")
        # if self.cleaned_data.get("status") == Answer.CORRECT:
            # self.cleaned_data["grade"] = 0
            # 
            # 
        # if self.cleaned_data.get("status") == Answer.ALMOST_CORRECT:
            # return 0.8
        # 
        # if self.cleaned_data.get("status") == Answer.ALMOST_INCORRECT:
            # return 0.4
        # 
        # if self.cleaned_data.get("status") == Answer.INCORRECT:
            # return 0.2
        # 
        # return self.cleaned_data.get("status")
    def is_valid(self):
        return True

def get_answer_form(*args, **kwargs):
    user = kwargs.get("user", None)
    if user and user.is_superuser:
        return SuperuserAnswerFormSimplified(instance=kwargs.get("instance"))

    return AnswerForm(*args, **kwargs)