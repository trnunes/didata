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

    
def to_csv(classroom, topic):
    students_grades = topic.calculate_grades(classroom)
    description = topic.topic_title
    type = "Trabalho"
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    csv = [[classroom.academic_site_id, description, type, date]]

    for student, grade in students_grades:
        if student.profile.student_id:
            csv.append([student.profile.student_id, grade])
    return csv

def csv_to_academico(file, milestone, login, password):
    import csv
    import undetected_chromedriver.v2 as uc
    uc.TARGET_VERSION = 106
    student_grades = []
    diary = ""
    task = ""
    type = ""
    date = ""
    with open(file, newline='') as csv_file:
        reader = csv.reader(csv_file)
        student_grades = []
        for index, row in enumerate(reader):
            
            if index == 0:
                
                diary = row[0]
                task = row[1]
                type = row[2]
                date = row[3]
                continue
            student_grades.append([row[0], row[1]])
        
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
                input_nota_aluno.send_keys("{:2.1f}".format(float(grade)).replace(".", ","))
            except:                    
                erros.append(student_grade)
            

        browser.find_element("xpath", "//input[@value='Salvar']").click()
    except:
        print("Algo deu errado no lançamento")
    
    
    return erros





if __name__=="__main__":
    file_name = sys.argv[1]
    login = sys.argv[2]
    password = sys.argv[3]
    milestone = sys.argv[4]
    csv_to_academico(file_name, milestone, login, password)