import os
import copy
# from django_rq import job
from .nlp_operations import *
import unidecode
import csv
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import TextIOWrapper
import itertools
import pickle
import pandas as pd
from django.conf import settings
from django_rq import job

def read_lines(path, storage, include_header=False, useIOWrapper=True):
    
    tmp_file = os.path.join(settings.MEDIA_ROOT, path)
    data = pd.read_excel(tmp_file)
    lines = []
    if include_header:
        header = []
        for c in data:
            header.append(c)
        lines.append(header)
    for t in data.itertuples():
        lines.append(list(t[1:]))
 
    return lines

def read_grades(path, storage, useIOWrapper = True):
    grades = read_lines(path, storage, useIOWrapper=useIOWrapper)
    

    grades_transposed = [[] for g in grades[0]]
    for answers_grade in grades:
        for i, grade_text in enumerate(answers_grade):
            if grade_text:
                grades_transposed[i].append(grade_text)

    return grades_transposed

def check_spell(answers_matrix):
    from hunspell import Hunspell
    h = Hunspell('Portuguese (Brazilian)', hunspell_data_dir=r'./hunspell_dicts')

    csv_content = []
    header = ["Alunos", "Redações"]
    for i, answer_row in enumerate(answers_matrix[1:]):
        
        student = answer_row[0]
        corrected_tokens = []
        correction_row = [student]
        
        for j, answer in enumerate(answer_row[1:]):
            tokens = tokenize(answer)
            for t in tokens:
                if h.spell(t):
                    corrected_tokens.append(t)
                else:
                    corrected_tokens.append(t + str(h.suggest(t)))
                    
            corrected_answer = " ".join(corrected_tokens)
            correction_row.append(corrected_answer)
            
        csv_content.append(correction_row)
        # break

    
    return csv_content


@job
def assess(answers_matrix, grade_file_path="", phrases_per_question=[], score_function=score_keywords):
    # global should_log 
    # answers_matrix = read_lines(answers_file_path, default_storage, True)
    correction_grades = phrases_per_question
    if grade_file_path:
        correction_grades = read_grades(grade_file_path, default_storage)
    
    csv_content = []
    header = ["Alunos e Correções / Questões"]

    questions = [a for a in answers_matrix[0]][1:]
    obs_header = [["Nota", "Correções"] for q in questions]
    header = []
    for q, obs_header in zip(questions, obs_header):
        header.append(q)
        header += obs_header
    header.insert(0, "Alunos/Correções")
    
    csv_content.append(header)
    
    for i, answer_row in enumerate(answers_matrix[1:]):
        
        student = answer_row[0]
        correction_row = [student]
        
        for j, answer in enumerate(answer_row[1:]):
            
            if pd.isnull(answer):
                answer = ""

            if j >= len(correction_grades):
                break
            # print("Correction Grades: ")
            # print(correction_grades)
# 
            # print("CORRECTIONS J: ", correction_grades[j])
            # import pdb; pdb.set_trace()
                
            grade = list(score_function(answer, correction_grades[j]))

            
            correction_row.append(answer)
            
            correction_row.append(grade[0])
            
            if grade[1]:
                correction_row.append("Faltou mencionar os seguintes conceitos: %s"%str(grade[1]))
            else:
                correction_row.append("")
        csv_content.append(correction_row)
        # break

    
    return csv_content

# print(score(test_sentence, [ref_sentence], "", domain_phrases))
# print(score_keywords(test_sentence, domain_phrases))