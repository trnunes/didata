from django import template
from ..models import ResourceRoom
from django.urls import reverse
register = template.Library()

@register.simple_tag
def is_on_resource_room(student):
	return ResourceRoom.objects.filter(students__id__exact=student.id).exists()

@register.simple_tag
def get_resource_room_url(student):
	rroom = ResourceRoom.objects.filter(students__id__exact=student.id).first()
	url = reverse('mydidata:resource_room_topics', args= (rroom.uuid, True))
	return url

@register.simple_tag
def get_student(error):
	return error[0]

@register.simple_tag
def get_grade(error):
	return error[1]
