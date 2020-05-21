from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def get_answers(question, student, test=None):
    answers = question.answer_set.filter(student=student)
    if test:
        answers = answers.filter(test=test)
    
    return answers
    
@register.simple_tag
def get_question_status(question, student, test=None):
    if get_answers(question, student, test):
        return "Respondida!"
    else:
        return ""
        
@register.simple_tag
def get_choice_label_class(answer, choice):
    if answer.choice == choice and answer.choice.is_correct:
        return "label label-success"
    if answer.choice == choice and not answer.choice.is_correct:
        return "label label-danger"
    if choice.is_correct:
        return "label label-success"
    
        
@register.simple_tag
def is_selected(choice, answer):
    if choice == answer.choice:
        return "true"
    else:
        return "false"

@register.simple_tag
def get_copy_detect_url(question):
    return reverse('mydidata:detect_copies', args= (question,))

@register.simple_tag
def get_answer_url(question, test):
    return question.get_answer_url(test)

@register.simple_tag
def get_next_answer_url(question, test):
    return question.next_answer_url(test)

@register.simple_tag
def append_test_param(action_url, test):
    return action_url + "?test=" + str(test.id)