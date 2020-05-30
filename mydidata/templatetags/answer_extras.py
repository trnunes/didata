from django import template
from ..models import Answer
register = template.Library()

    
@register.simple_tag
def get_topic_percent(student_dict, student):
	return student_dict.get(student)

@register.simple_tag
def get_topic(topic_percent):
	return topic_percent[0]

@register.simple_tag
def get_percent(topic_percent):
	return topic_percent[1]