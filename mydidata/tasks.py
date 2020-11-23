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

def go_academico():
    str_login = "trnunes"
    str_senha = "thi@g0rinu"
    hash_db = {}

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = settings.GOOGLE_CHROME_PATH
    browser = webdriver.Chrome(executable_path=settings.CHROMEDRIVER_PATH, chrome_options=chrome_options)

    #login
    browser.get("http://www.academico.iff.edu.br")
    browser.find_element_by_partial_link_text("PROFESSOR").click()
    browser.find_element_by_xpath("//input[@name='LOGIN']").send_keys(str_login)
    browser.find_element_by_xpath("//input[@name='SENHA']").send_keys(str_senha)
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
    etapa = "1BIM"
    diario = "161148"
    while not achei:
        try:
            link_diario = browser.find_element_by_xpath("//a[contains(@href,'"+ manutencao_pauta+"') and contains(@href,'"+ diario.strip() + "') and contains(@href, '"+ etapa.strip()+"')]")
            achei = True
        except:
            pass            

    link_diario.click()

    av_desc = "Avaliação Teste"
    av_type = "Trabalho"
    av_date = "20/11/2020"

    input = browser.find_element_by_xpath("//input[contains(@value, 'Inserir')]")
    input.click()
    sel = Select(browser.find_element_by_xpath("//select[contains(@name, 'TIPO')]"))
    desc = browser.find_element_by_xpath("//input[contains(@name, 'DESC')]")
    date = browser.find_element_by_xpath("//input[contains(@name, 'DT')]")

    sel.select_by_visible_text("Trabalho")
    desc.send_keys(av_desc)
    date.send_keys(av_date)

    input = browser.find_element_by_xpath("//input[contains(@value, 'Inserir')]")
    input.click()
    lancar_notas = browser.find_element_by_xpath("//td[contains(., av_desc)]/following-sibling::td/a[contains(., 'Lançar')]")

    lancar_notas.click()
