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
from .models import Answer
import requests
from django.shortcuts import get_object_or_404
import json

@background(schedule=60)
def count_words(text):
    return len(text.split(" "))

@background(schedule=0)
def correct_answers(answers_list):

    for answer_id in answers_list:
        answer_obj = get_object_or_404(Answer, pk=answer_id)
        if answer_obj.question.expected_output:
            return answer_obj.correct_c_programming_answer()
            
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

        response = requests.post("http://pontuando.herokuapp.com/mydidata/assess_answers/", json=json_req)
        print("ERROR: ", response.content)
        response_json = response.json()

        answer_obj.feedback = response_json["results"][0]["corrections"]
        grade = response_json["results"][0]['grade']

        if grade > 8:
            answer_obj.evaluate(Answer.CORRECT)
        elif grade > 6 and grade <= 8:
            answer_obj.evaluate(Answer.ALMOST_CORRECT)
        elif grade > 3 and grade <= 6:
            answer_obj.evaluate(Answer.ALMOST_INCORRECT)
        else:
            answer_obj.evaluate(Answer.INCORRECT)
        print(response_json)
        # except:
            # print("ERROR: ", json_req)
            # 
            # pass

    
def to_csv(classroom, topic):
    students_grades = topic.calculate_grades(classroom)
    description = topic.topic_title
    type = "trabalho"
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    csv = [[classroom.academic_site_id, description, type, date]]

    for student, grade in students_grades:
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
    browser = uc.Chrome(version_main=106)
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