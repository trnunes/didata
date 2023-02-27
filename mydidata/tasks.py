from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.keys import Keys
import time
import datetime
from datetime import date
import sys
import codecs
import re
import unidecode
from django.conf import settings
from background_task import background
from .models import Answer, Profile
import requests
from django.shortcuts import get_object_or_404
import json
from .nlp_analyzer import score_keywords, score, assess, read_lines, normalize
from .models import Classroom
from celery import shared_task
from django.utils import timezone
from django.utils.html import format_html
from django.core.mail import send_mail
from django.template import Template, Context

def send_alert_email(classroom, students):
    # Get the teachers related to the classroom
    teachers = classroom.teachers.all()
    teacher_emails = [teacher.email for teacher in teachers]

    # Build the email body HTML
    student_template = Template('<li><h3>{{ student_name }}</h3><ul>{% for alert in alerts %}<li><span style="color:red">{{ alert }}</span></li>{% endfor %}</ul></li>')
    student_alerts = [student_template.render(Context({'student_name': student.first_name + f"({student.username})", 'alerts': student.profile.alerts.split(";")})) for student in students]
    email_body = '<h2>Alertas para a Turma {}</h2><ul>{}</ul>'.format(classroom.name, ''.join(student_alerts))


    # Send the email
    print(teacher_emails)
    subject = '[AprendaFazendo] Alertas para Turma {}'.format(classroom.name)
    recipient_list = teacher_emails
    send_mail(subject, '', "", recipient_list, html_message=email_body)









@shared_task
def diagnose(classroom_id):
    classroom = get_object_or_404(Classroom.objects.prefetch_related("students"), pk=classroom_id)
    student_alerts = []
    students = classroom.students.all()
    current_datetime = timezone.now()
    deadlines = classroom.deadlines.all()
    for student in students:
        try:
            student.profile
        except Exception:
            Profile.objects.create(user=student, actions_log="Criado em %s"%timezone.localtime().strftime("%d/%m/%Y às %H:%M:%S"))

        # Get the datetime one week ago from the current datetime
        one_week_ago = current_datetime - timezone.timedelta(weeks=1)
        student.profile.alerts = ""
        # Compare the last login datetime to one week ago
        if student.last_login < one_week_ago:
            # Do something if the last login was more than a week ago
            alert_msg = "Usuário não acessa há mais de uma semana;"
            print(student.first_name)
            print(alert_msg)
            student.profile.alerts += "Usuário não acessa há mais de uma semana;"
            student_alerts.append(student)
    
    
        for deadline in deadlines:
            if deadline.due_datetime < current_datetime and not deadline.topic.has_completed(student):
                alert_msg = f"Estudante não cumpriu prazo limite de envio de atividades para o tópico:  {deadline.topic.topic_title};"
                print(student.first_name)
                print(alert_msg)
                student.profile.alerts += alert_msg
                student_alerts.append(student)
        
        message = analyze_time_spent_on_topics(student)
        
        if message:
            student.profile.alerts += message
            student_alerts.append(student)
        
        student.save()

    
    send_alert_email(classroom, student_alerts)


def analyze_time_spent_on_topics(user):
    topic_times_dict = {}
    alerts = ""
    if user.profile and user.profile.actions_log:
        actions = user.profile.actions_log.split(";")
        topic_time_actions = [a for a in actions if "Tempo gasto" in a]
        for time_action in topic_time_actions:
            minute_seconds = time_action.split("=")[-1].split(" s")[0].split("em")[0].strip()
            topic = time_action.split('"')[-1].split('"')[0]
            if not topic_times_dict.get(topic, None):
                topic_times_dict[topic] = 0
            print("TIME ACTION: ", time_action)
            print("MINUTES AND SECONDS: ", minute_seconds)
            
            topic_times_dict[topic] += time_to_seconds(minute_seconds)
        
        for topic, time in topic_times_dict.items():
            if time < 5 * 60:
                alerts +=  f'Tempo gasto no tópico "{topic}" inferior a 5 min: {time} seconds;'
    return alerts

def time_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds

def detect_text_uri(uri):
    """Detects text in the file located in Google Cloud Storage or on the Web.
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = uri

    response = client.text_detection(image=image,image_context={"language_hints": ["pt"]})
    texts = response.text_annotations
    print('Texts:')
    full_text = ""
    for text in texts:
        full_text += '<br>"{}"'.format(text.description)

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    return full_text


@background(schedule=60)
def count_words(text):
    return len(text.split(" "))

def detect_copies(answers):
    # import pdb;pdb.set_trace()
    punishing_questions = set([a.question for a in answers if a.question.punish_copies])
    
    
    all_answers_set = Answer.objects.filter(question__in=punishing_questions).exclude(id__in=[a.id for a in answers]).all()
    result_dict = {}
    for a1 in answers:
        for a2 in all_answers_set:
            if (
                a1.text_escaped() == a2.text_escaped()
                
            ):
                if not result_dict.get(a1, None):
                    result_dict[a1] = [a1]
                result_dict[a1].append(a2)
    return list(result_dict.values())

    



@background(schedule=0)
def correct_answers(answers_list):


    for answer_obj in answers_list:

        if answer_obj.question.expected_output:
            answer_obj.correct_c_programming_answer()
            continue
        
        if answer_obj.question.choices.all():
            answer_obj.correct()
            continue
            
        keywords = answer_obj.question.ref_keywords.split(";")
        if not answer_obj.question.ref_keywords:
            continue
        json_req = {
            "answers": [
                {
                    "student": 1,
                    "text": answer_obj.text_escaped()
                }
            ],
            "ref_answers": [keywords] 
        }

        # try:
        answer_matrix = [["Students", "Question"]]
        for a in json_req["answers"]:
            answer_matrix.append([a['student'], a['text']])
        ref_answers = json_req["ref_answers"]
        results = assess(answer_matrix, phrases_per_question=ref_answers, score_function=score_keywords)
        json_results = []
        for i in range(1,  len(results)):
            
            json_response = {
                "student": results[i][0],
                "answer": results[i][1],
                "grade": results[i][2],
                "corrections": results[i][3],
            }
            json_results.append(json_response)


        answer_obj.feedback = json_response["corrections"]
        grade = json_response['grade']

        if grade > 8:
            answer_obj.evaluate(Answer.CORRECT)
        elif grade > 6 and grade <= 8:
            answer_obj.evaluate(Answer.ALMOST_CORRECT)
        elif grade > 3 and grade <= 6:
            answer_obj.evaluate(Answer.ALMOST_INCORRECT)
        else:
            answer_obj.evaluate(Answer.INCORRECT)
        print(json_response)
        # except:
            # print("ERROR: ", json_req)
            # 
            # pass

    
def to_csv(classroom, topic):
    students_grades = topic.calculate_grades(classroom)
    description = topic.topic_title
    type = "Trabalho"
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    csv = [[classroom.academic_site_id, description, type, date]]

    for student, grade in students_grades:
        if student.profile:
            if student.profile.student_id:
                csv.append([student.profile.student_id, grade])
    return csv

def csv_to_academico(file, login, password):
    import csv
    import undetected_chromedriver.v2 as uc
    student_grades = []
    diary = ""
    task = ""
    type = ""
    date = ""
    with open(file, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        student_grades = []
        for index, row in enumerate(reader):
            if index == 0:
                diary = row[0]
                task = row[1]
                type = row[2]
                date = row[3]
                next
            student_grades.append([row[0], row[1]])
        
    browser = uc.Chrome()
    # browser = webdriver.Firefox(executable_path="./geckodriver")
    #login    
    try:
        browser.get("http://www.academico.iff.edu.br")

        browser.find_element(by=By.PARTIAL_LINK_TEXT, value="PROFESSOR").click()
        browser.find_element("xpath", "//input[@name='LOGIN']").send_keys(login)
        browser.find_element("xpath", "//input[@name='SENHA']").send_keys(password)
        browser.find_element("xpath", "//input[@name='Submit']").click()

        achei = False
        while not achei:
            try:
                link = browser.find_element(by=By.PARTIAL_LINK_TEXT, value="Meus") # Meus Diarios
                achei = True
            except:
                pass

        link.click()

        # tempo para aparecer os diários
        time.sleep(2)


        erros = []

        link_diario = None    
        achei = False
        manutencao_pauta = "3068"
        while not achei:
            try:
                link_diario = browser.find_element("xpath", "//a[contains(@href,'"+ manutencao_pauta+"') and contains(@href,'"+ diary.strip() + "') and contains(@href, '"+ milestone.strip()+"')]")
                achei = True
            except:
                pass            

        link_diario.click()

        av_desc = task
        av_type = type
        av_date = date
        try:
            lancar_notas = browser.find_element("xpath", "//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
        except:
            input = browser.find_element("xpath", "//input[contains(@value, 'Inserir')]")
            input.click()
            sel = Select(browser.find_element("xpath", "//select[contains(@name, 'TIPO')]"))
            desc = browser.find_element("xpath", "//input[contains(@name, 'DESC')]")
            date = browser.find_element("xpath", "//input[contains(@name, 'DT')]")

            sel.select_by_visible_text(av_type)
            desc.send_keys(av_desc)
            date.send_keys(av_date)

            input = browser.find_element("xpath", "//input[contains(@value, 'Inserir')]")
            input.click()

        lancar_notas = browser.find_element("xpath", "//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
        lancar_notas.click()

        for student_grade in student_grades:
            student = student_grade[0]
            grade = student_grade[1]
            try:
            
                input_nota_aluno = browser.find_element("xpath", "//a[text()='%s']/../..//input[contains(@name, 'NOTA')]" % student)
                input_nota_aluno.send_keys(Keys.BACKSPACE*10)
                input_nota_aluno.send_keys("{:2.1f}".format(grade).replace(".", ","))
            except:                    
                erros.append(student_grade)
            # import pdb;pdb.set_trace()

        browser.find_element("xpath", "//input[@value='Salvar']").click()
    except:
        print("Algo deu errado no lançamento")
    browser.close()
    return erros




def go_academico(students_grades, assessment, milestone, diary, login, password):
    import undetected_chromedriver.v2 as uc
    browser = uc.Chrome()
    # browser = webdriver.Firefox(executable_path="./geckodriver")
    #login    
    try:
        browser.get("http://www.academico.iff.edu.br")

        browser.find_element(by=By.PARTIAL_LINK_TEXT, value="PROFESSOR").click()
        browser.find_element("xpath", "//input[@name='LOGIN']").send_keys(login)
        browser.find_element("xpath", "//input[@name='SENHA']").send_keys(password)
        browser.find_element("xpath", "//input[@name='Submit']").click()

        achei = False
        while not achei:
            try:
                link = browser.find_element(by=By.PARTIAL_LINK_TEXT, value="Meus") # Meus Diarios
                achei = True
            except:
                pass

        link.click()

        # tempo para aparecer os diários
        time.sleep(2)


        erros = []

        link_diario = None    
        achei = False
        manutencao_pauta = "3068"
        while not achei:
            try:
                link_diario = browser.find_element("xpath", "//a[contains(@href,'"+ manutencao_pauta+"') and contains(@href,'"+ diary.strip() + "') and contains(@href, '"+ milestone.strip()+"')]")
                achei = True
            except:
                pass            

        link_diario.click()

        av_desc = assessment.get("description", "")
        av_type = assessment.get("type", "Trabalho")
        av_date = assessment.get("date")
        try:
            lancar_notas = browser.find_element("xpath", "//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
        except:
            input = browser.find_element("xpath", "//input[contains(@value, 'Inserir')]")
            input.click()
            sel = Select(browser.find_element("xpath", "//select[contains(@name, 'TIPO')]"))
            desc = browser.find_element("xpath", "//input[contains(@name, 'DESC')]")
            date = browser.find_element("xpath", "//input[contains(@name, 'DT')]")

            sel.select_by_visible_text(av_type)
            desc.send_keys(av_desc)
            date.send_keys(av_date)

            input = browser.find_element("xpath", "//input[contains(@value, 'Inserir')]")
            input.click()

        lancar_notas = browser.find_element("xpath", "//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
        lancar_notas.click()

        for student_grade in students_grades:
            student = student_grade[0]
            grade = student_grade[1]
            try:
                student.profile
            except:
                erros.append(student_grade)
                continue

            try:
            
                input_nota_aluno = browser.find_element("xpath", "//a[text()='%s']/../..//input[contains(@name, 'NOTA')]" % student.profile.student_id)
                input_nota_aluno.send_keys(Keys.BACKSPACE*10)
                input_nota_aluno.send_keys("{:2.1f}".format(grade).replace(".", ","))
            except:                    
                erros.append(student_grade)
            # import pdb;pdb.set_trace()

        browser.find_element("xpath", "//input[@value='Salvar']").click()
    except:
        print("Algo deu errado no lançamento")
    browser.close()
    return erros

def correct_whole_topic(class_id, topic_uuid):
    import undetected_chromedriver.v2 as uc
    from time import sleep
    import time
    username = 'tnunes'
    password ='m1l@b0t&lh0'

    driver = uc.Chrome()

    driver.delete_all_cookies()
    driver.get("https://www.aprendafazendo.net/mydidata/login/")


    sleep(2)


    driver.find_element("id",'id_username').send_keys(username)
    driver.find_element("id",'id_password').send_keys(password)

    driver.find_element("xpath",'//input[@type="submit"]').click()
    sleep(2)
    driver.get("https://www.aprendafazendo.net/mydidata/topic_progress/%s/%s"%(class_id, topic_uuid))

    els = driver.find_elements("xpath", '//i[contains(@class, "cloud")]/..')
    els += driver.find_elements("xpath", '//i[contains(@class, "triangle")]/..')
    links = [l.get_attribute("href") for l in els]
    for l in links:
        driver.get("https://www.aprendafazendo.net/mydidata/get_corrections/" + l.split("/")[-1])
    
    driver.close()

if __name__=="__main__":
    file_name = sys.args[0]
    login = sys.args[1]
    password = sys.args[2]
    csv_to_academico(file_name, login, password)