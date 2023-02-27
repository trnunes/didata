# -*- coding: utf-8 -*-
from random import choices
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm
from django.forms.models import ModelMultipleChoiceField

from .models import Deadline, Reply, ForumPost, Comment, ContentVersion, Team, Topic, Question, Profile, Choice, Discipline, Classroom, Answer, TestUserRelation
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import modelform_factory, formset_factory, inlineformset_factory, modelformset_factory
from django.contrib.auth.models import User
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms.widgets import DateTimeInput
from bootstrap_datepicker_plus.widgets import DateTimePickerInput


from django.db.models import Q

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
    enrollment = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control',} ), label="Matrícula", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['password2']
    

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

class DeadlineForm(forms.ModelForm):
    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.all(),
        widget=forms.RadioSelect(),
        required=True
        
    )
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=forms.HiddenInput,
        required=True
    )


    class Meta:
        model = Deadline
        fields = ('due_datetime', 'topic', 'classroom',)
        widgets = {
            'due_datetime': DateTimePickerInput(),


        }

class TopicForm(forms.ModelForm):


    class Meta:
        model = Topic
        fields = ('topic_title', 'label','topic_content', 'order', )
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
    
    def is_valid(self):
        return super(TopicForm, self).is_valid() and self.owner
        

    def __init__(self, *args, **kwargs):
        if kwargs.get("owner", None):
            self.owner = kwargs.pop("owner")
        super().__init__(*args, **kwargs)


        # self.fields['owner'] =  forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=User.objects.all(), label="Selecione o dono do tópico", empty_label=None, )

    def save(self, *args, **kwargs):
        instance = super(TopicForm, self).save(*args, **kwargs, commit=False)
        instance.owner = self.owner
        instance.save()
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

class CProgrammingQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("question_text", 'difficulty_level', 'question_type', "is_team_work", "test_inputs", "expected_output", "weight", "punish_copies",)
        widgets = {
            'question_text': forms.CharField(widget=CKEditorUploadingWidget(), label='Enunciado'),
            'expected_output': forms.TextInput(
                attrs={
                    'placeholder':'Digite as saídas esperadas para cada entrada separadas por vírgula',
                    'class':'col-md-12 form'
                }
            ),
            'test_inputs': forms.TextInput(
                attrs={
                    'placeholder':'Digite as entradas de teste separadas por vírgula.',
                    'class':'col-md-12 form'
                }
            ),
            'difficulty_level': forms.Select(
                attrs={'placeholder':'Dificuldade', 'class':'form-control'}
            ),
            'question_type': forms.Select(
                attrs={'placeholder':'Tipo', 'class':'form-control'}
            ),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        # widgets = {
            # "body": forms.CharField(widget=CKEditorUploadingWidget, label='Texto')
        # }
    
    
 
CommentFormSet = inlineformset_factory(
    Topic,
    Comment,
    CommentForm,
    can_delete = False,
    min_num=2,
    extra=0
)

class PostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ("title", "content",)
        widgets = {
            'content': forms.CharField(widget=CKEditorUploadingWidget, label='Texto'),
        }
        
    title = forms.CharField(
        required=True, widget=forms.TextInput(attrs={'class':'form-control'})
    )
    

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ("content",)

RepliesFormSet = inlineformset_factory(
    ForumPost,
    Reply,
    ReplyForm,
    can_delete = False,
    min_num=2,
    extra=0
)

class DiscursiveQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("question_text", 'difficulty_level', 'question_type', "is_team_work", "weight", "ref_keywords", "punish_copies", "should_block_paste", )
        widgets = {
            'question_text': forms.CharField(widget=CKEditorUploadingWidget, label='Enunciado'),
            'ref_keywords': forms.TextInput(
                attrs={
                    'placeholder':'Digite as palavras-chave separadas por ponto e vírgula (;)',
                    'class':'col-md-12 form'
                }
            ),
            'difficulty_level': forms.Select(
                attrs={'placeholder':'Dificuldade', 'class':'form-control'}
            ),
            'question_type': forms.Select(
                attrs={'placeholder':'Tipo', 'class':'form-control'}
            ),
        }
        
class MultipleChoiceQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question_text', 'difficulty_level', 'question_type', "is_team_work",)
        widgets = {
            'question_text': forms.CharField(widget=CKEditorUploadingWidget, label='Enunciado'),
            
            'difficulty_level': forms.Select(
                attrs={'placeholder':'Dificuldade', 'class':'form-control'}
            ),
            'question_type': forms.Select(
                attrs={'placeholder':'Tipo', 'class':'form-control'}
            ),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', "is_correct"]

    def __init__(self, *args, **kwargs)    :
        super(ChoiceForm, self).__init__(*args, **kwargs)
        self.fields["choice_text"] = forms.CharField(widget=CKEditorUploadingWidget, label='Digite a alternativa:')
    

MultipleChoiceQuestionFormSet = modelformset_factory(Question, form=MultipleChoiceQuestionForm, extra=1, can_delete=True)
ChoiceFormSet = modelformset_factory(Choice, form=ChoiceForm, extra=1)

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
        fields = ('assignment_file','answer_text', 'choice', 'team',)

        widgets = {
            'answer_text' : forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
            # 'choice': forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=Choice.objects.none(), label="Selecione a sua resposta", empty_label=None)
        }
        labels = {
            'answer_text': 'Digite sua Resposta Aqui',
            'assignment_file': 'Arquivo da Resposta',            
        }
    
    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)
        self.question = kwargs.pop('question', None)
        self.test = kwargs.pop('test', None)
        if not self.user:
            raise ValidationError("You should specify a user as named arg for this form!")
        
        if not self.question:
            raise ValidationError("You should specify a question as named arg for this form!")

        answerFindCriteria = {}
        
        if self.user:
            answerFindCriteria["student"] = self.user

        if self.question:
            answerFindCriteria["question"] = self.question

        if self.test:
            answerFindCriteria["test"] = self.test

        answer = Answer.objects.filter(**answerFindCriteria).first()
        
        if answer:
            kwargs["instance"] = answer
        
        
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        if self.question.is_multiple_choice():
            self.fields['choice'] = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=Choice.objects.filter(question=self.question), label="Selecione a sua resposta", empty_label=None)
            self.fields.pop('answer_text', None)
            self.fields.pop('assignment_file', None)
        
        # self.fields['choice'] = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=self.question.choice_set, label="Selecione a sua resposta", empty_label=None)
        if self.question and (self.question.is_discursive() or self.question.is_c_programming()):
            
            self.fields.pop('choice', None)
        
        if self.question and self.question.file_upload_only:
            self.fields.pop('answer_text', None)
        if self.question.is_team_work:
            
            msg = """
                Você deve selecionar uma equipe para enviar. 
                Caso ainda não possua, clique no menu "Minhas Equipes" e crie uma. 
                Você também pode pedir para participar de alguma equipe dos seus colegas ;-)
            """
            error_messages={'required': msg}
            self.fields['team'] = forms.ModelChoiceField(widget=forms.RadioSelect(), queryset=Team.objects.filter(members__id = self.user.id), required=True, label="Selecione uma equipe", error_messages=error_messages)

        else:
            self.fields.pop("team", None)
    
    def clean_assignment_file(self):

        file = self.cleaned_data.get("assignment_file")
        
        if not file and not self.question.file_types_accepted:
            return file

        if not file and self.question.file_types_accepted:
            raise ValidationError(_("Você deve enviar um arquivo como anexo a esta questão! Clique no botão \"Escolher Arquivo\" e depois envie a resposta."))
        
        file_type = file.name.split(".")[-1]
        if self.question.file_types_accepted and not file_type in self.question.file_types_accepted and not "todos" in self.question.file_types_accepted:
            raise ValidationError(_("Arquivo de resposta inválido para esta questão. Apenas os tipos %(tipos)s são aceitos!"), 
                params = {'tipos': str(self.question.file_types_accepted)},
            )
        return file
    
    def clean_answer_text(self):
        student = self.user
        classrooms = Classroom.objects.filter(students__id = student.id).all()
        question = self.question
        topic = question.topic
        test = self.test
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
    
    def save(self, *args, **kwargs):

        self.instance = super(AnswerForm, self).save(*args, **kwargs, commit=False)
        self.instance.question = self.question
        self.instance.student= self.user
        
        if self.test:
            self.instance.test = self.test
        
        self.instance.save()
        return self.instance

class SuperuserAnswerFormSimplified(forms.ModelForm):
    status = forms.ChoiceField(widget=forms.RadioSelect, choices=Answer.EVAL_CHOICES)
    graphic_annotations = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = Answer
        fields = [ "assignment_file", 'feedback', "status", 'grade', 'graphic_annotations' ]
        field_order = ["feedback", "status", "grade"]
        labels = {}
        labels['feedback'] = 'Correções Aqui'
    
    def is_valid(self):
        return True

def get_answer_form(*args, **kwargs):
    user = kwargs.get("user", None)
    if user and user.is_superuser:
        return SuperuserAnswerFormSimplified(instance=kwargs.get("instance"))

    return AnswerForm(*args, **kwargs)

class UserMultipleChoiceField(FilteredSelectMultiple):
    """
    Custom multiple select Feild with full name
    """                                                                                                                                                                 
    def label_from_instance(self, obj):

        return "%s %s" % (obj.first_name, obj.last_name)

    
class TeamForm(forms.ModelForm):



    class Media:
        # Django also includes a few javascript files necessary
        # for the operation of this form element. You need to
        # include <script src="/admin/jsi18n"></script>
        # in the template.
        css = {
                'all': ('/static/admin/css/widgets.css',),
            }
        js = ('/admin/jsi18n',)

    
    class Meta:
        model = Team
        fields = ["name", "members", "owner"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        team_member_choices_query = User.objects
        classroom_ids = [c.id for c in Classroom.objects.filter(students__id=self.user.id)]
        if self.user and classroom_ids:
            team_member_choices_query = User.objects.filter(classrooms__id__in= classroom_ids)

        super(TeamForm, self).__init__(*args, **kwargs)
        
        
        self.fields['members'] = forms.ModelMultipleChoiceField(queryset=team_member_choices_query.all(), widget=UserMultipleChoiceField("Estudantes", is_stacked=False))

    
    
    def save(self, *args, **kwargs):
        team = super(TeamForm, self).save(*args, **kwargs)
        team.members.set(self.cleaned_data['members'])
        team.save()
        return team

class ClassroomForm(forms.ModelForm):
    class Media:
        # Django also includes a few javascript files necessary
        # for the operation of this form element. You need to
        # include <script src="/admin/jsi18n"></script>
        # in the template.
        css = {
                'all': ('/static/admin/css/widgets.css',),
            }
        js = ('/admin/jsi18n',)

    class Meta:
        model = Classroom
        fields = ['name', 'academic_site_id', 'students', 'disciplines', 'teachers']
        widgets = {
            'students': forms.CheckboxSelectMultiple(),
            'disciplines': forms.CheckboxSelectMultiple()
        }
    
    def __init__(self, *args, **kwargs):
        super(ClassroomForm, self).__init__(*args, **kwargs)
        self.fields['students'] = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=UserMultipleChoiceField("Estudantes", is_stacked=False), required=False)
        self.fields['disciplines'] = forms.ModelMultipleChoiceField(queryset=Discipline.objects.all(), widget=UserMultipleChoiceField("Disciplinas", is_stacked=False))
        self.fields['teachers'] = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=UserMultipleChoiceField("Professores Responsáveis", is_stacked=False))
    
    def save(self, *args, **kwargs):
        classroom = super(ClassroomForm, self).save(*args, **kwargs)
        classroom.students.set(self.cleaned_data['students'])
        classroom.disciplines.set(self.cleaned_data['disciplines'])
        classroom.save()
        return classroom
