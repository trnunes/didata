from django import template
register = template.Library()
from django.urls import reverse

@register.simple_tag
def get_close_url(classroom, test):
	return reverse('mydidata:test_close', args= (classroom.id, test.uuid))
	
@register.simple_tag
def is_test_closed(classroom, test):
	return test in classroom.closed_tests.all()
	
@register.simple_tag
def get_open_url(classroom, test):
	return reverse('mydidata:test_open', args= (classroom.id, test.uuid))

@register.simple_tag
def get_progress_url(classroom, test):
	return reverse('mydidata:test_progress', args = (classroom.id, test.uuid))

@register.simple_tag
def get_assess_url(classroom, test):
	return reverse('mydidata:test_assess', args= (classroom.id, test.uuid))

@register.simple_tag
def get_grades_url(classroom, test):	
	return reverse('mydidata:calculate_grades', args=(classroom.id, test.uuid))