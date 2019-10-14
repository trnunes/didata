# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Topic, Question, DiscursiveAnswer, Discipline
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class SubscriberForm(UserCreationForm):
    first_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={'class':'form-control'})
    )
    last_name = forms.CharField(
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
    password2 = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control', 'type':'password'})
    )
    # disciplines = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple)
    # def __init__(self,*args,**kwargs):
    #     print kwargs
    #     self.classroom = kwargs.pop('classroom')
    #     super(SubscriberForm,self).__init__(*args,**kwargs)
    #     self.fields['disciplines'] = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple, choices=self.classroom.disciplines.all().values_list('id', 'name'))



class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('topic_title', 'topic_content', 'order')
        widgets = {
            'topic_title': forms.TextInput(
                attrs={
                    'placeholder':'Title',
                    'class':'col-md-12 form-control'
                }
            ),
            'topic_content': forms.Textarea(
                attrs={
                    'placeholder':'Conteúdo',
                    'class':'form-control'
                }
            ),
            'order': forms.TextInput(
                attrs={
                    'placeholder':'Ordem',
                    'class':'gi-form-addr form-control'
                }
            ),
        }
        
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
class DiscursiveAnswerForm(forms.ModelForm):


    class Meta:
        model = DiscursiveAnswer
        fields = ['assignment_file','answer_text',]

        widgets = {
            'answer_text' : forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
        }
        labels = {
            'answer_text': 'Digite sua Resposta Aqui',
            'assignment_file': 'Arquivo da Resposta',
        }
    def clean_assignment_file(self):

        file = self.cleaned_data.get("assignment_file")
        question = self.instance.question
        if not file and not question.file_types_accepted:
            return file

        if not file and question.file_types_accepted:
            raise ValidationError(_("Você deve enviar um arquivo como anexo a esta questão! Clique no botão \"Escolher Arquivo\" e depois envie a resposta."))

        print("FILE: ", file)
        file_type = file.name.split(".")[-1]
        if question.file_types_accepted and not file_type in question.file_types_accepted and not "todos" in question.file_types_accepted:
            raise ValidationError(_("Arquivo de resposta inválido para esta questão. Apenas os tipos %(tipos)s são aceitos!"), 
                params = {'tipos': str(question.file_types_accepted)},
            )        
        return file
    
    def clean_answer_text(self):
        question = self.instance.question
        text = self.cleaned_data.get("answer_text")
        print("TEXTO: ", text)
        if question.text_required and not text:
            raise ValidationError(_("Sua resposta não pode ser em branco! Por favor, escreva a sua reposta na caixa de texto abaixo."))
        return text





class SuperuserDiscursiveAnswerForm(forms.ModelForm):

    class Meta:
        model = DiscursiveAnswer
        fields = ['answer_text', 'assignment_file']

        widgets = {
            'answer_text': forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
        }
        labels = {
            'answer_text': 'Resposta Aqui',
        }

        fields += ['feedback', 'is_correct']
        widgets['feedback'] = forms.CharField(widget=CKEditorUploadingWidget(), label="Correções",
                                              required=False)
        labels['feedback'] = 'Correções Aqui'
        labels['is_correct'] = "Está Correta?"

    def is_valid(self):
        return True;

