# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Topic, Question, DiscursiveAnswer, Discipline
from ckeditor_uploader.widgets import CKEditorUploadingWidget


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
        fields = ('answer_text', 'assignment_file',)
        widgets = {
            'answer_text' : forms.CharField(widget=CKEditorUploadingWidget(), label="Resposta", required=False),
        }
    
    def is_valid(self):
        return True;
        
