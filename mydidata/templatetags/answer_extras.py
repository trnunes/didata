from django import template
from ..models import MultipleChoiceAnswer
register = template.Library()

@register.simple_tag
def get_specific_answer(answer):
    try:
        return answer.multiplechoiceanswer
    except (MultipleChoiceAnswer.DoesNotExist):
        return answer.discursiveanswer