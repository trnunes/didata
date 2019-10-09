from django import template
from ..models import MultipleChoiceAnswer
register = template.Library()

@register.simple_tag
def get_specific_answer(answer):
    try:
        return answer.multiplechoiceanswer
    except (MultipleChoiceAnswer.DoesNotExist):
        return answer.discursiveanswer

@register.simple_tag
def get_topic_percent(student_dict, student):
	return student_dict.get(student)

@register.simple_tag
def get_topic(topic_percent):
	return topic_percent[0]

@register.simple_tag
def get_percent(topic_percent):
	return topic_percent[1]