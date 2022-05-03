from django import template
register = template.Library()
from django.urls import reverse

@register.simple_tag
def get_deadline(topic, classroom):
	return topic.get_deadline_for(classroom)

@register.simple_tag
def get_clasroom_list(students):
	return set([klass for student in students for klass in student.classroom_set.all()])

@register.simple_tag
def get_close_url(classroom, topic):
	return reverse('mydidata:topic_close', args= (classroom.id, topic.uuid))
	
@register.simple_tag
def is_topic_closed(classroom, topic):
	return topic in classroom.closed_topics.all()

@register.simple_tag
def test_is_closed(classroom, test):
	return test in classroom.closed_tests.all()
	
@register.simple_tag
def get_open_url(classroom, topic):
	return reverse('mydidata:topic_open', args= (classroom.id, topic.uuid))

@register.simple_tag
def get_progress_url(classroom, topic):
	return reverse('mydidata:topic_progress', args = (classroom.id, topic.uuid))

@register.simple_tag
def get_assess_url(classroom, topic):
	return reverse('mydidata:topic_assess', args= (classroom.id, topic.uuid))

@register.simple_tag
def get_grades_url(classroom, topic):	
	return reverse('mydidata:calculate_grades', args=(classroom.id, topic.uuid))

@register.simple_tag
def get_test_progress(classroom, test):
	return reverse('mydidata:test_progress', args=(test.uuid, classroom.id))