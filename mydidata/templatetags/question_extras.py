from django import template

register = template.Library()

@register.simple_tag
def get_answers(question, student):
    answers = question.answer_set.filter(student=student)
    if student.first_name == "Marcela":
        print(student, ": ", question.topic.topic_title, " : ", question.question_text)
        print(" Answers: ", set(answers))
    return question.answer_set.filter(student=student)
    
@register.simple_tag
def get_question_status(question, student):
    if get_answers(question, student):
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
        return "label label-info"
    
        
@register.simple_tag
def is_selected(choice, answer):
    if choice == answer.choice:
        return "true"
    else:
        return "false"
    