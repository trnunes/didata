from django import template
register = template.Library()
from django.urls import reverse

@register.simple_tag
def get_close_url(classroom, test):
	return reverse('mydidata:test_close', args= (classroom.id, test.uuid))
	
@register.simple_tag
def is_test_closed(classroom, test):
	if not classroom:
		return False
	return test in classroom.closed_tests.all()
	
@register.simple_tag
def get_open_url(classroom, test):
	return reverse('mydidata:test_open', args= (classroom.id, test.uuid))

@register.simple_tag
def get_progress_url(classroom, test):
	return reverse('mydidata:test_progress', args = (test.uuid, classroom.id))

@register.simple_tag
def get_assess_url(classroom, test):
	return reverse('mydidata:test_assess', args= (classroom.id, test.uuid))

@register.simple_tag
def is_closed_for_student(user, test):
    
    return test.is_closed_for(user)

@register.simple_tag
def get_finish_url_for_user(classroom, test):
	return reverse('mydidata:finish_test', args=(classroom.id, test.uuid))

@register.simple_tag
def get_test_user(student_grades_dict, student):
	return student_grades_dict[student].get('test_user', None)

@register.simple_tag
def is_closed(test, classroom):
	return test.is_closed(classroom)
	
@register.simple_tag
def get_class(test, user):
	if not user.is_superuser:
		classes = [c for c in test.classrooms.all() if c in user.classrooms.all()]
	else:
		classes = test.classrooms.all()


	return classes