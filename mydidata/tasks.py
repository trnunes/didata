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

def go_academico(students_grades, assessment, milestone, diary, login, password):
    chrome_options = webdriver.ChromeOptions()
    
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = settings.GOOGLE_CHROME_PATH
    browser = webdriver.Chrome(executable_path=settings.CHROMEDRIVER_PATH, chrome_options=chrome_options)
    # browser = webdriver.Firefox(executable_path="./geckodriver")
    #login    
    browser.get("http://www.academico.iff.edu.br")
    browser.find_element_by_partial_link_text("PROFESSOR").click()
    browser.find_element_by_xpath("//input[@name='LOGIN']").send_keys(login)
    browser.find_element_by_xpath("//input[@name='SENHA']").send_keys(password)
    browser.find_element_by_xpath("//input[@name='Submit']").click()

    achei = False
    while not achei:
        try:
            link = browser.find_element_by_partial_link_text("Meus") # Meus Diarios
            achei = True
        except:
            pass

    link.click()
    # tempo para aparecer os diários
    time.sleep(2)

    print("------CADASTRANDO NOTAS---------")

    erros = []

    link_diario = None    
    achei = False
    manutencao_pauta = "3068"
    while not achei:
        try:
            link_diario = browser.find_element_by_xpath("//a[contains(@href,'"+ manutencao_pauta+"') and contains(@href,'"+ diary.strip() + "') and contains(@href, '"+ milestone.strip()+"')]")
            achei = True
        except:
            pass            

    link_diario.click()

    av_desc = assessment.get("description", "")
    av_type = assessment.get("type", "Trabalho")
    av_date = assessment.get("date")
    try:
        lancar_notas = browser.find_element_by_xpath("//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
    except:
        input = browser.find_element_by_xpath("//input[contains(@value, 'Inserir')]")
        input.click()
        sel = Select(browser.find_element_by_xpath("//select[contains(@name, 'TIPO')]"))
        desc = browser.find_element_by_xpath("//input[contains(@name, 'DESC')]")
        date = browser.find_element_by_xpath("//input[contains(@name, 'DT')]")

        sel.select_by_visible_text(av_type)
        desc.send_keys(av_desc)
        date.send_keys(av_date)

        input = browser.find_element_by_xpath("//input[contains(@value, 'Inserir')]")
        input.click()
    
    lancar_notas = browser.find_element_by_xpath("//td[contains(., '%s')]/following-sibling::td/a[contains(., 'Lançar')]"%av_desc)
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
        
            input_nota_aluno = browser.find_element_by_xpath("//a[text()='%s']/../..//input[contains(@name, 'NOTA')]" % student.profile.student_id)
            input_nota_aluno.send_keys(Keys.BACKSPACE*10)
            input_nota_aluno.send_keys("{:2.1f}".format(grade).replace(".", ","))
        except:                    
            erros.append(student_grade)
        # import pdb;pdb.set_trace()

    browser.find_element_by_xpath("//input[@value='Salvar']").click()
    browser.close()
    print("Errors: ", erros)
    return erros