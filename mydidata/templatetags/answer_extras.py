from django import template

from ..views import feedback
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

@register.simple_tag
def get_icon_class(answer, user):
	
	url = answer.get_detail_url()
	
	if user.is_superuser:
		url = answer.feedback_url()

	if answer.is_sent():
		return [url, "color: blue", "bi bi-cloud-check"]
	if answer.is_ok():
		return [url, "color: blue", "bi bi-check-circle-fill"]
	
	return [url, "color: red", "bi bi-exclamation-triangle-fill"]
		
												
		