from __future__ import with_statement
from ast import With

from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from .models import ContentVersion, Question, Choice, Topic, Test, Discipline, Classroom, ResourceRoom, Answer, TestUserRelation, Profile, Deadline, Team
from django.template import loader
from django.http import Http404
from django.urls import reverse
import sys
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from background_task.models import Task
from django.views import View

from .nlp_analyzer import score_keywords, score, assess, read_lines
from .forms import ContentVersionForm, SuperuserAnswerFormSimplified, TopicForm, SubscriberForm, ProfileForm, UserUpdateForm, TopicForm, MultipleChoiceQuestionForm, DiscursiveQuestionForm, AnswerFormUploadOnly, AnswerForm, MultipleChoiceQuestionFormSet, ChoiceFormSet, CProgrammingQuestionForm, TeamForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.conf import settings
from django.contrib import messages
from django.db import transaction
import boto3
import re
import json
from django.db.models import Q
import csv
from .tasks import go_academico, correct_answers, correct_whole_topic, to_csv
import datetime
from django.utils import timezone
from datetime import timedelta
import requests
from django.http import JsonResponse
import subprocess
import os
from django.views.decorators.csrf import csrf_exempt

def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser, login_url='/mydidata/login/')(view_func)
    return decorated_view_func


class HomePage(TemplateView):
    """
    Because our needs are so simple, all we have to do is
    assign one value; template_name. The home.html file will be created
    in the next lesson.
    """
    template_name = 'mydidata/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomePage, self).get_context_data(*args, **kwargs)
        desc_orderd_topics = list(Topic.objects.filter(publish_date__isnull=False, visible=True).order_by('-publish_date')) 
        
        odd_topics = [desc_orderd_topics[i] for i in range(1, len(desc_orderd_topics), 2)]
        even_topics = [desc_orderd_topics[i] for i in range(2, len(desc_orderd_topics), 2)]
        context['topics_left'] = odd_topics
        context['topics_right'] = even_topics
        categories = list(set([c for t in Topic.objects.all() for c in t.subject.split(",")]))
        categories_right = [categories[i] for i in range(0, len(categories), 2)]
        categories_left = [categories[i] for i in range(1, len(categories), 2)]
        

        context['categories_right'] = categories_right
        context['categories_left'] = categories_left
        
        context['main'] = desc_orderd_topics[0]

        return context


class ClassList(ListView):
    model = Classroom
    template_name = 'mydidata/class_list.html'
    context_object_name = 'class_list'
    
    def get_queryset(self):        
        return Classroom.objects.all().order_by('name')
        
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(ClassList, self).dispatch(*args, **kwargs)
        
class ResourceRoomList(ListView):
    model = Classroom
    template_name = 'mydidata/class_list.html'
    context_object_name = 'class_list'
    
    def get_queryset(self):        
        return ResourceRoom.objects.all().order_by('name')
        
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(ResourceRoomList, self).dispatch(*args, **kwargs)

class TestList(ListView):
    model = Test
    template_name = 'mydidata/test_list.html'
    context_object_name = 'tests'

    def get_queryset(self):
    	user = self.request.user
    	classes = Classroom.objects.filter(students__id=user.id).order_by('name').all()
    	tests = []
    	
    	if not user.is_superuser:
    		[tests.extend(c.tests.all()) for c in classes]
    	else:
    		tests = Test.objects.all().order_by('title')
    	return tests

    
    def dispatch(self, *args, **kwargs):
        return super(TestList, self).dispatch(*args, **kwargs)

class AdsView(View):
    
    def get(self, request, *args, **kwargs):
        line  ="google.com, pub-3262579547697172, DIRECT, f08c47fec0942fa0"
        return HttpResponse(line)
        

class TopicList(ListView):
    model = Topic
    template_name = 'mydidata/topic_list.html'
    context_object_name = 'topics'

    def get_queryset(self):
        discipline_id = self.request.GET.get('discipline', None)
        resource_room_only = self.request.GET.get('resource_room_only', False) == "True"
        discipline = Discipline.objects.get(uuid=discipline_id)
        topic_list = Topic.objects.filter(discipline=discipline, is_resource=resource_room_only, is_assessment=False, visible=True).order_by('order')
        
        return topic_list
    def dispatch(self, *args, **kwargs):
        return super(TopicList, self).dispatch(*args, **kwargs)
        
class DisciplineList(ListView):
    model = Discipline
    template_name = 'mydidata/discipline_list.html'
    context_object_name = 'disciplines'

    def get_queryset(self):
        # if self.request.user.is_authenticated:
            # discipline_list = []
            # classrooms = Classroom.objects.filter(students__id=self.request.user.id)
            # discipline_list = set([d for klass in classrooms for d in klass.disciplines.order_by('name').all()])
            # 
        # else:
        discipline_list = Discipline.objects.filter(enabled=True).order_by('name')
        return discipline_list
        

    def dispatch(self, *args, **kwargs):
        return super(DisciplineList, self).dispatch(*args, **kwargs)

def content(request, label):
    topics = Topic.objects.filter(label=label)
    if topics:
        return HttpResponseRedirect(reverse('mydidata:topic_detail', args=(topics.first().uuid,)))
    return render('mydidata/home.html')

@login_required
def topic_edit(request, topic_uuid):
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    discipline = topic.discipline
    form = ContentVersionForm(instance=topic, user=request.user)
    
    if request.POST:
        form = ContentVersionForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("mydidata:topic_detail", args=(topic.uuid,)))
    return render(request, 'mydidata/topic_edit.html', context={'form': form})

@login_required
def version_edit(request, version_id):
    version = get_object_or_404(ContentVersion, pk=version_id)
    
    if request.POST:
        version_form = ContentVersionForm(request.POST, instance=version, user=request.user)
        if version_form.is_valid():
            version_form.save()
            return HttpResponseRedirect(reverse('mydidata:version_detail', args=(version.id,)))
    
    version_form = ContentVersionForm(instance=version, user=request.user)
    
    return render(request, 'mydidata/version_edit.html', context={'form': version_form})

@login_required
def version_detail(request, version_id):
    version = get_object_or_404(ContentVersion, pk=version_id)
    return render(request, 'mydidata/version_detail.html', context={'version': version})


@login_required
def version(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)

    if request.POST:
        form = ContentVersionForm(request.POST, topic=topic, user=request.user)
        if form.is_valid():
            saved_version = form.save()
            return HttpResponseRedirect(reverse('mydidata:version_detail', args=(saved_version.id,)))
    else:
        form = ContentVersionForm(topic=topic, user=request.user)
        filtered_versions = ContentVersion.objects.filter(topic=topic, user=request.user, approved=False)
        if filtered_versions.exists():
            return HttpResponseRedirect(reverse('mydidata:version_edit', args=(filtered_versions.first().id,)))
            

        
    return render(request, "mydidata/version.html", context={'form': form})
        
def version_list(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    return render(request, 'mydidata/version_list.html', context={"topic": topic})

def version_compare(request, version_id):
    version = get_object_or_404(ContentVersion, pk=version_id)
    return render(request, "mydidata/version_compare.html", context={"version": version})

def version_update(request, version_id):
    version = get_object_or_404(ContentVersion, pk=version_id)
    version.replace_topic()
    return HttpResponseRedirect(reverse("mydidata:topic_detail", args=(version.topic.uuid,)))

@login_required
def topic(request, discipline_uuid):
    discipline = get_object_or_404(Discipline, uuid=discipline_uuid)
    print("post", request.POST)
    if request.POST:
        form = TopicForm(request.POST, owner=request.user)
        
        if form.is_valid():

            instance = form.save()
            instance.discipline = discipline
            instance.save()
            print(instance.topic_title)
            return HttpResponseRedirect(reverse("mydidata:topic_detail", args=(form.instance.uuid,)))
        else:
            print("Errors", form.errors)
        
    else:
        form = TopicForm(owner=request.user)
    return render(request, "mydidata/topic.html", context={"form": form})

    

@login_required
def academico(request, class_id, topic_uuid):
    classroom = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    diary = str(classroom.academic_site_id)
    if request.POST:
        login = request.POST.get('username')
        password = request.POST.get('password')
        milestone= request.POST.get('etapa')
        if not diary:
            return
        assessment = {
            'description': topic.topic_title,
            'type': 'Trabalho',
            'date': datetime.datetime.now().strftime("%d/%m/%Y")
        }
        students_grades = topic.calculate_grades(classroom)
        errors = []
        
        errors = go_academico(students_grades, assessment, milestone, diary, login, password)
        
        return render(request, 'mydidata/academico_results.html', {'classroom': classroom, 'title': topic.topic_title, 'errors': errors})

def download_grades_by_topic(request, class_id, topic_uuid):
    classroom = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)

    filename = "notas.csv"
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = "attachment; filename=\"%s\""%filename
    writer = csv.writer(response)
    writer.writerows(to_csv(classroom, topic))

    return response


def correct_the_whole_topic(request, class_id, topic_uuid):
    correct_whole_topic(class_id, topic_uuid)
    return redirect('mydidata:class_progress', class_id=class_id, )


def search(request):
    keyword = request.GET['keyword']
    if(not keyword):
        return render('mydidata/home.html')
    context = {'topics': Topic.objects.filter(Q(topic_title__icontains=keyword) | Q(topic_content__icontains=keyword)).order_by('topic_title') }
    return render(request, 'mydidata/search.html', context)

def topic_next(request, current_id):
    topic = get_object_or_404(Topic, pk=current_id)
    next_topic = topic.next()
    if not next_topic:
        return HttpResponseRedirect('/mydidata/topics?discipline=' + topic.discipline.uuid)
    return HttpResponseRedirect(reverse('mydidata:topic_detail', args=(next_topic.uuid,)))
    
def topics_by_subject(request):
    subject = request.GET.get("subject", None)
    topics = Topic.objects.filter(Q(subject__icontains=subject), visible=True).order_by("-publish_date")
    return render(request, 'mydidata/topic_list.html', {'topics': topics})

def subscriber_new(request, classroom_id, template='mydidata/subscriber_new.html'):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    if request.method == 'POST':
        
        form = SubscriberForm(request.POST)
        
        if form.is_valid():
            # Unpack form values
            first_name = form.cleaned_data['first_name']            
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data['email']
            # Create the User record
            user = User(first_name=first_name, username=username, email=email)
            user.set_password(password)
            
            user.save()
            
            # disciplines = form.cleaned_data['disciplines']
            
            for discipline in classroom.disciplines.all():
                discipline.students.add(user)
                discipline.save()
                
            classroom.students.add(user)
            classroom.save()
            # Create Subscriber Record
            # Auto login the user
            return HttpResponseRedirect('/mydidata/login')
    else:
        
        form = SubscriberForm()

    return render(request, template, {'form':form, 'classroom':classroom})

@login_required
@transaction.atomic
def update_profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.user != user and not request.user.is_superuser:
        messages.error(request, "Você não tem autorização para alterar este usuário!")
        render(request, 'mydidata/profile')
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance = user)
        profile_form = ProfileForm(request.POST, instance = user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            first_name = user_form.cleaned_data['first_name']            
            username = user_form.cleaned_data['username']
            email = user_form.cleaned_data['email']
            # Create the User record
            user.username = username
            user.first_name = first_name
            user.email = email
            
            user.save()
            
            profile_form.save()
            messages.success(request, "O usuário foi devidamente cadastrado!")
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo')
        return render(request, 'mydidata/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
    else:
        user_form = UserUpdateForm(instance=user)
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
            profile.save()
        profile_form = ProfileForm(instance=user.profile)
        return render (request, 'mydidata/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
        

def topic_close(request, topic_uuid, class_id):
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass.closed_topics.add(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def topic_open(request, topic_uuid, class_id):
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass.closed_topics.remove(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def topic_assess(request, topic_uuid, class_id):
    classroom = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    discipline_list = classroom.disciplines.all()
    topics = []
    student_list = classroom.students.all().order_by('first_name');
    
    for discipline in discipline_list:
        topics.extend(discipline.topic_set.all())
    topics.sort(key=lambda topic: topic.order)
    
    for student in student_list:
        for q in topic.question_set.all():
            answers = Answer.objects.filter(student=student, question=q).all()            
            for a in answers:
                a.correct()
                a.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def test_close(request, uuid, class_id):
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=uuid)
    klass.closed_topics.add(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def test_open(request, uuid, class_id):
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=uuid)
    klass.closed_topics.remove(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def close_test_for_student(request, test_id, student_id):
    test = get_object_or_404(Test, pk=test_id)
    student = get_object_or_404(User, pk=student_id)
    tuserrelation = TestUserRelation.objects.filter(test=test,user=student).first()
    tuserrelation.close()
    return redirect('mydidata:student_progress', test_id=test_id, student_id=student_id )

def test_assess(request, uuid, class_id):
    classroom = get_object_or_404(Classroom, pk=class_id)
    test = get_object_or_404(Test, uuid=uuid)
    student_list = classroom.students.all().order_by('first_name')
    for student in student_list:
        for q in test.questions.all():
            answers = Answer.objects.filter(student=student, question=q, test=test).all()
            
            for a in answers:
                a.correct()
    return redirect('mydidata:test_progress', class_id=class_id, uuid=test.uuid)

@login_required
def progress(request, discipline_name):
    discipline = Discipline.objects.get(name=discipline_name)
    topics = discipline.topic_set.all()
    return render(request, 'mydidata/progress.html', {'topics':topics,})

@login_required
def topic_progress(request, topic_uuid, class_id):
    user = request.user
    students = [user]
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    discipline = topic.discipline
    if user.is_superuser:
        students = klass.students.all().order_by('first_name')
    return render(request, 'mydidata/topic_progress.html', {'classroom': klass, 'students': students, 'topics':[topic],})

@login_required
def finish_test(request, uuid, class_id, key):
    user = request.user
    test = get_object_or_404(Test, uuid=uuid)
    if key != test.key:
        response_context = {'error':"Palavra-chave errada!"}
        return HttpResponse(json.dumps(response_context), content_type='application/json')

    klass = get_object_or_404(Classroom, pk=class_id)
    test_user = TestUserRelation.objects.filter(test=test, student=user).first()
    if test_user: 
        test_user.is_closed = True
        test_user.save()
    return HttpResponse(json.dumps({}), content_type='application/json')
    #return redirect('mydidata:test_progress', class_id=class_id, uuid=test.uuid)


@login_required
def resource_room_progress(request, uuid):
    r_room = get_object_or_404(ResourceRoom, uuid=uuid)
    students = r_room.students.all()
    topics = r_room.topics.all()    
    return render(request, 'mydidata/topic_progress.html', {'students': students, 'topics':topics,})

@login_required 
def my_progress(request, discipline_uuid):
    discipline = get_object_or_404(Discipline, uuid=discipline_uuid)

    student = request.user
    topics = []

    topics.extend(Topic.objects.filter(discipline=discipline, is_assessment=False).order_by('order'))
    
    klass = Classroom.objects.filter(students__id = request.user.id).first()
    r_klass = ResourceRoom.objects.filter(students__id = request.user.id).first()
    if r_klass:
    	topics.extend(r_klass.topics.all())
    topics.sort(key=lambda topic: topic.order)
    return render(request, 'mydidata/my_progress.html', {'classroom': klass, 'students': [student] , 'topics':topics,})
    
@login_required
def class_progress(request, class_id):
    classroom = get_object_or_404(Classroom, pk=class_id)
    discipline_list = classroom.disciplines.all()
    topics = []
    students = classroom.students.all().order_by('first_name');
    
    for discipline in discipline_list:
        topics.extend(discipline.topic_set.all())
    topics.sort(key=lambda topic: topic.order)
    return render(request, 'mydidata/progress.html', {'classroom': classroom, 'students': students, 'topics':topics,})

@login_required
def percentage_progress(request, class_id):
    classroom = get_object_or_404(Classroom, pk=class_id)
    discipline_list = classroom.disciplines.all()
    topics = []
    student_list = classroom.students.all().order_by('first_name');
    
    for discipline in discipline_list:
        topics.extend(discipline.topic_set.all())
    topics.sort(key=lambda topic: topic.order)
    student_by_topic_percentage = {}
    student_by_topic_grade = {}
    for student in student_list:
        student_by_topic_percentage[student] = []
        for topic in topics:
            answers = [Answer.objects.filter(student=student, question=q).first() for q in topic.question_set.all()]
            answers = [a for a in answers if a]
            percentage = len(answers)/len(topic.question_set.all()) if len(topic.question_set.all()) else 0            
            student_by_topic_percentage[student].append([topic,  "{:2.1f}%".format(percentage*100)])

       
    return render(request, 'mydidata/percentage_progress.html', {'topics': topics, 'topic_dict': student_by_topic_percentage})

@login_required
def calculate_grades(request, class_id, topic_uuid):
    classroom = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    students_grades = topic.calculate_grades(classroom)
    return render(request, 'mydidata/percentage_progress.html', {'topic': topic, 'classroom': classroom, 'students_grades': students_grades})

@login_required
def test_to_academico(request, class_id, test_uuid):
    test = get_object_or_404(Test, uuid=test_uuid)
    classroom = get_object_or_404(Classroom, pk=class_id)    

    grades_by_student = test.calculate_grades(classroom)

    diary = str(classroom.academic_site_id)

    if request.POST:
        login = request.POST.get('username')
        password = request.POST.get('password')
        milestone= request.POST.get('etapa')
        if not diary:
            return
        assessment = {
            'description': test.title,
            'type': 'Prova',
            'date': datetime.datetime.now().strftime("%d/%m/%Y")
        }
        students_grades = []
        for student in grades_by_student.keys():
            students_grades.append((student, grades_by_student[student]['grade']))

        errors = []
        
        errors = go_academico(students_grades, assessment, milestone, diary, login, password)
        
        return render(request, 'mydidata/academico_results.html', {'classroom': classroom, 'title': test.title, 'errors': errors})



@login_required
def test_answer(request, question_uuid, test_id):
    question = get_object_or_404(Question, uuid=question_uuid)
    test = get_object_or_404(Test, pk=test_id)
    tuserrelation = test.get_or_create_test_user_relation(request.user)
    
    if request.POST:
        form = AnswerForm(request.POST, request.FILES, question=question, test=test, user=request.user)
        
        answer = Answer.objects.filter(student=request.user, question=question).first()
        if answer:
            context={
                "error_msg": """
                    Você deve finalizar essa tentativa antes de enviar uma nova resposta. 
                    Siga para a próxima questão.
                """,
                "next_link": tuserrelation.get_next_answer_url(question),
                "form": form
            }
            if not context['next_link']:

                context['next_link'] = reverse('mydidata:student_progress', args=(test.id,request.user.id,))
            return render(request, 'mydidata/answer_error.html', context)



        if tuserrelation.is_closed:
            return HttpResponseRedirect(reverse('mydidata:test_detail', args=(test.uuid,)))
        
        
        if form.is_valid():
            form.save()

            if tuserrelation.get_next_answer_url(question):
                print("NEXT URL: ", tuserrelation.get_next_question(question))

                return HttpResponseRedirect(tuserrelation.get_next_answer_url(question))
            print("NEXT URL: ", reverse('mydidata:test_detail', args=(test.uuid,)))

            return redirect('mydidata:student_progress', student_id=request.user.id, test_id=test.id)
            
            #redirect to_test detail
    else:
        form = AnswerForm(question=question, test=test, user=request.user)
        context = {
            "question": question,
            "test": test,
            "form": form
        }

        return render(request, "mydidata/answer_cru.html", context)
    
    return HttpResponseRedirect(reverse('mydidata:test_detail', args=(test.uuid,)))
        


@login_required
def answer(request, question_uuid):

    question = get_object_or_404(Question, uuid=question_uuid)
    
    if request.user.is_authenticated:
        classrooms = Classroom.objects.filter(students__id = request.user.id)
        for klass in classrooms:
            closed_topics = klass.closed_topics.all()
            if question.topic in closed_topics:
                return redirect(question.topic.get_absolute_url())

    if request.POST:
        if not request.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
                #TODO insert test logic here
        
        form = get_answer_form(request.POST, request.FILES, instance=answer, question=question)
        
        answer = form.instance
        answer.status = Answer.SENT
        
        redirect_url = question.topic.get_absolute_url()
        
        if request.FILES.get('assignment_file', False):
            file_name = request.FILES['assignment_file'].name
            request.FILES['assignment_file'].name = answer.get_answer_file_id() + "." +  file_name.split(".")[-1]
        
        if form.is_valid():
            form.save()

            #TODO insert logic for team work

        else:
            context = {
                'question': question,            
                'form': form,
            }
            return render(request, 'mydidata/answer_cru.html', context)
        if question.is_discursive():
            form = SuperuserAnswerFormSimplified(instance = answer)
            # return render(request, 'mydidata/discursive_answer_detail.html', {'answer': answer, 'form': form, "next": redirect_url})
            return HttpResponseRedirect(question.topic.get_absolute_url_questionary_anchor())

        return HttpResponseRedirect(redirect_url)


    if request.user.is_authenticated:
        answer = Answer.find(student=request.user, question=question, test=test)
        form = get_answer_form(instance=answer, question=question, user=request.user)

    context = {
        'question': question,        
        'form': form,
    }
    return render(request, 'mydidata/answer_cru.html', context)



def discursive_answer_detail(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)

    topic_questions = answer.question.topic.get_ordered_questions()
    answers_by_question = {}
    
    answers_by_question.update([(q, None) for q in topic_questions])

    answers = Answer.objects.filter(question__id__in=[q.id for q in topic_questions], student=request.user)
    [answers_by_question.__setitem__(a.question, a) for a in answers]

    return render(request, 'mydidata/discursive_answer_detail.html', {'answers_by_question': answers_by_question, 'answer': answer, "form": SuperuserAnswerFormSimplified(instance=answer)})

@login_required()
def multiple_choice_answer_detail(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)
    return render(request, 'mydidata/multiple_choice_answer_detail.html', {'answer':answer,})



@login_required()
def feedback(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question
    form = SuperuserAnswerFormSimplified(instance=answer)
    classroom = Classroom.objects.filter(students__id=answer.student.id).first()

    next_answer_for_student_url = reverse('mydidata:class_progress', args=(classroom.id,))
    
    next_student_answer = answer.get_next_answer_for_class(classroom) or reverse('mydidata:class_progress', args=(classroom.id,))

    next_answer_for_student = answer.get_next_for_student()
    
    if(next_answer_for_student):
        next_answer_for_student_url = reverse('mydidata:feedback', args=(next_answer_for_student.id,))
    

    if request.POST:
        form = SuperuserAnswerFormSimplified(request.POST, instance=answer)
        form.save()
        context = {
            'question': question,
            'form': form,
            'answer': answer,
            'classroom': classroom,
            'next_student_answer_url': next_student_answer,
            'next_answer_url': next_answer_for_student_url,
            'action_url': reverse('mydidata:feedback', args=(answer_id,)),
        }
        return HttpResponseRedirect(request.POST.get("redirect_to"))

    context = {
        'question': question,
        'form': form,
        'action_url': reverse('mydidata:feedback', args=(answer_id,)),
        'next_student_answer_url': next_student_answer,
        'next_answer_url': next_answer_for_student_url,
    }
    return render(request, 'mydidata/answer_cru.html', context)

@login_required()
def multiple_choice_answer(request, question_uuid):
    #TODO remove duplicated code with #discursive_answer
    question = get_object_or_404(Question, uuid=question_uuid)

    if request.POST:
        form = AnswerForm(request.POST, request.FILES, question=question, user=request.user)
        if form.is_valid():
            answer = form.save()
            answer.status = Answer.SENT
            answer.save()
            return redirect(answer.get_detail_url())
        else:
            context = {
                'question': question,
                'form': form
            }
            return render(request, "mydidata/answer_cru.html", context)
            

    else:
        form = AnswerForm(question=question, user=request.user)
        context = {
            "form": form,
            "question": question
        }
        return render(request, "mydidata/answer_cru.html", context)
        


@login_required()
def discursive_answer(request, question_uuid):
    question = get_object_or_404(Question, uuid=question_uuid)
    topic = question.topic
    user = request.user
    
    if topic.is_closed_for(user):
        return redirect(topic.get_absolute_url())
    
    
    
    if request.POST:
        form = AnswerForm(request.POST, request.FILES, question=question, user=user)
        
        if form.is_valid():
            answer = form.save()
            answer.status = Answer.SENT
            answer.save()
            save_and_get_feedback_input_pressed = "save_and_feedback" in request.POST
            
            if save_and_get_feedback_input_pressed:
                return redirect(reverse("mydidata:get_corrections", args=(answer.id,)))

            return redirect(answer.get_detail_url())
        else:
            context = {
                'question': question,
                'form': form
            }

            return render(request, "mydidata/answer_cru.html", context)
            
    
    form = AnswerForm(question=question, user=user)
    context = {
        'question': question,
        'form': form
    }
    
    return render(request, "mydidata/answer_cru.html", context)
    

@login_required()
def test_progress(request, uuid, class_id):
    test = get_object_or_404(Test, uuid=uuid)
    classroom = get_object_or_404(Classroom, pk=class_id)    
    students = []
    if not request.user.is_superuser:
        students = [request.user]
    else:
        students = classroom.students.all().order_by('first_name')

    grades_by_student = test.calculate_grades(classroom, students)
    
    return render(request, 'mydidata/test_progress.html', {'classroom':classroom, 'students': students, 'test':test, 'student_grades': grades_by_student,})

@login_required()
def student_progress(request, test_id, student_id):
    test = get_object_or_404(Test, pk=test_id)
    student = get_object_or_404(User, pk=student_id)
    test_user = TestUserRelation.objects.get(test=test, student=student)
    return render(request, 'mydidata/test_progress.html', {'test_user': test_user, 'students': [student], 'test': test,})

@login_required()
def calculate_student_grades(request, test_id, student_id):
    test = get_object_or_404(Test, pk=test_id)
    student = get_object_or_404(User, pk=student_id)
    grades = test.calculate_grades_for_student(student)
    test_user = TestUserRelation.objects.get(test=test, student=student)
    return render(request, 'mydidata/test_progress.html', {'students': [student], 'test_user': test_user, 'test': test, 'student_grades': grades,})


@login_required()
def next_try(request, test_user_id):
    test_user_rel = get_object_or_404(TestUserRelation, pk=test_user_id)
    test = test_user_rel.test
    test.next_try(test_user_rel.student)
    print("TRIES", test_user_rel.tries)
    return HttpResponseRedirect(reverse("mydidata:start_test", args=(test.uuid,)))
    
@login_required()
def test_results_wavg(request, class_id, uuid):
    test = get_object_or_404(Test, uuid=uuid)
    students = [request.user]
    classroom = get_object_or_404(Classroom, pk=class_id)
    if request.user.is_superuser:
        students = classroom.students.all().order_by('first_name')
    student_grade = {}
    if test.is_closed(classroom):
        
        for student in students:
            total_weight = 0
            sum_weights = 0
            final_grade = 0
            for q in test.questions.all():
                answer = Answer.objects.filter(student=student, question=q, test=test).first()
                if answer: sum_weights += answer.grade * q.weight
                total_weight += q.weight
            final_grade = 0
            if sum_weights: final_grade = sum_weights/total_weight

            student_grade[student] = "{:2.1f}".format(final_grade*10)
        

    return render(request, 'mydidata/test_results.html', {'classroom': classroom, 'students': students, 'test':test, 'student_grades': student_grade})

@login_required()
def test_results_sum(request, class_id, uuid):
    test = get_object_or_404(Test, uuid=uuid)
    students = [request.user]
    classroom = get_object_or_404(Classroom, pk=class_id)
    if request.user.is_superuser:
        students = classroom.students.all().order_by('first_name')
    student_grade = {}
    #TODO duplicated code with test_results_wavg()
    if test.is_closed(classroom):
        
        for student in students:
            
            sum_weights = 0
            final_grade = 0
            for q in test.questions.all():
                answer = Answer.objects.filter(student=student, question=q, test=test).first()
                if answer: sum_weights += answer.grade
                
            final_grade = 0
            if sum_weights: final_grade = sum_weights

            student_grade[student] = "{:2.1f}".format(final_grade)
        

    return render(request, 'mydidata/test_results.html', {'classroom': classroom, 'students': students, 'test':test, 'student_grades': student_grade})

def topic_detail(request, uuid):
    topic = Topic.objects.get(uuid=uuid)
    topic.topic_content = topic.topic_content.replace("<iframe", "<iframe allowfullscreen=\"allowfullscreen\"")
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', topic.topic_content)
    for url in urls:
        if url.find("upload") >= 0 :
            new_url = settings.UPLOAD_URL + "/uploads" + url.split("uploads")[-1]
            #TODO remove this replace
            new_url = new_url.replace("/https%3A//mydidata.s3.amazonaws.com", "")

            topic.topic_content = topic.topic_content.replace(url, new_url)


    questions = list(Question.objects.filter(topic=topic).order_by('index'))
    test_user_relation = None
    test = topic.test_set.all().first()
    if( test and request.user.is_authenticated):
        test_questions = test.questions.all()
        test_user_relation = TestUserRelation.objects.filter(test=test, student=request.user).first()
        if (not test_user_relation):
            test_user_relation = TestUserRelation.objects.create(student=request.user, test=test)
    
    context = {
        'topic': topic,
        'questions': questions,
        'test_user_relation': test_user_relation
    }
    if request.user.is_authenticated:
        klass = Classroom.objects.filter(students__id = request.user.id).first()
        context['classroom'] = klass

        if topic.has_assessment_question and questions:
            context['question'] = questions[0]
            questions = questions[1:]
    
    return render(request, 'mydidata/topic_detail.html', context)

@login_required
def start_test(request, uuid):
    test = get_object_or_404(Test, uuid=uuid)
    test_user = test.get_or_create_test_user_relation(request.user)
    first_question = test_user.current_questions()[0]
    print("URL: ", first_question.get_answer_url_for_test(test))
    return HttpResponseRedirect(first_question.get_answer_url_for_test(test))

    
@login_required
def test_detail(request, uuid):
    test = get_object_or_404(Test, uuid=uuid)

    classroom = Classroom.objects.filter(students__id=request.user.id).first()    
    questions = list(test.questions.order_by('index').all())
    tu = test.get_or_create_test_user_relation(request.user)
    


    reordered_questions = [questions[i-1] for i in tu.index_list_as_array()]

    context = {
        'questions': reordered_questions,
        'classroom': classroom,
        'test': test,

    }
    
    return render(request, 'mydidata/test_detail.html', context)

@login_required()
def test_new(request, topic_id):
    
    test = Test(student = request.user, difficulty_level = 1)
    topic = get_object_or_404(Topic, pk=topic_id)
    test.topic = topic
    test.save()
    questions = Question.objects.filter(topic=topic).filter(difficulty_level=1).order_by('?')[:5]
    for question in questions:
        test.questions.add(question)
    test.save()
    variables = {
        'test':test,
        'questions':questions,
    }
    template = 'mydidata/test_detail.html'
    return render(request, template, variables)
  
@login_required()
def question_detail(request, uuid):

    question = Question.objects.get(uuid=uuid)
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))', question.question_text)
    for url in urls:
        if url.find("upload"):
            new_url = settings.UPLOAD_URL + "/uploads/" + url.split("uploads")[-1]
            question.question_text = question.question_text.replace(url, new_url)

    return render(request, 
                'mydidata/question_detail.html', 
                {'question': question}
    )

@login_required()
@superuser_required
def multiple_choice_question(request, topic_uuid):

    topic = get_object_or_404(Topic, uuid=topic_uuid)

    if request.POST:
        questionform_set = MultipleChoiceQuestionFormSet(request.POST, prefix="question")
        choice_formset = ChoiceFormSet(request.POST, prefix='choice')

        if questionform_set.is_valid() and choice_formset.is_valid():
            for questionform in questionform_set:
                question = questionform.save()
                topic.question_set.add(question)
                topic.save()
                at_least_one_is_correct = False
                for choice_form in choice_formset:
                    choice = choice_form.save(commit=False)
                    at_least_one_is_correct |= choice.is_correct
                    choice.question = question
                    choice.save()
            
                if at_least_one_is_correct:
                    return redirect(topic)
                
                questionform.errors['__all__'] = questionform.error_class(['É necessário que pelo menos uma opção seja a correta. Marque a opção "É a alternativa correta?" de pelo menos uma opção'])
      
        context = {
            "question_formset": questionform_set,
            "choice_formset": choice_formset,
        }
        return render(request, "mydidata/multiple_choice_question_cru.html", context)
    else:

        question_formset = MultipleChoiceQuestionFormSet(prefix='question')
        choice_formset = ChoiceFormSet(prefix='choice')

        context = {
            "question_formset": question_formset,
            "choice_formset": choice_formset,
        }
        return render(request, "mydidata/multiple_choice_question_cru.html", context)

    
@login_required()
@superuser_required
def discursive_question(request, topic_uuid):
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    if request.POST:
        form = DiscursiveQuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            question.topic = topic
            question.save()
            return redirect(topic)
        
        return render(request, "mydidata/discursive_question_cru.html", {"form": form})

        
    else:
        form = DiscursiveQuestionForm()
        return render(request, "mydidata/discursive_question_cru.html", {"form": form})

@login_required()
@superuser_required
def c_programming_question(request, topic_uuid):
    topic = get_object_or_404(Topic, uuid=topic_uuid)

    if request.POST:
        form = CProgrammingQuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            question.topic = topic
            question.save()
            return redirect(topic)
        return render(request, "mydidata/c_programming_question_cru.html", {"form": form})
    else:
        form = CProgrammingQuestionForm()
        return render(request, "mydidata/c_programming_question_cru.html", {"form": form})
    
@superuser_required
def discursive_question_edit(request, uuid):
    question = get_object_or_404(Question, uuid=uuid)
    if request.POST:
        form = DiscursiveQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect(question.topic)
        
        return render(request, "mydidata/discursive_question_cru.html", {"form": form})

        
    else:
        form = DiscursiveQuestionForm(instance=question)
        return render(request, "mydidata/discursive_question_cru.html", {"form": form})

@superuser_required
def c_programming_question_edit(request, uuid):
    question = get_object_or_404(Question, uuid=uuid)
    if request.POST:
        form = CProgrammingQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect(question.topic)
        
        return render(request, "mydidata/c_programming_question_cru.html", {"form": form})

        
    else:
        form = CProgrammingQuestionForm(instance=question)
        return render(request, "mydidata/c_programming_question_cru.html", {"form": form})

@superuser_required
def multiple_choice_question_edit(request, uuid):
    question = get_object_or_404(Question, uuid=uuid)
    if request.POST:
        questionform_set = MultipleChoiceQuestionFormSet(request.POST, prefix="question", instance=question)
        choice_formset = ChoiceFormSet(request.POST, prefix='choice')

        if questionform_set.is_valid() and choice_formset.is_valid():
            for questionform in questionform_set:
                question = questionform.save()
                topic.question_set.add(question)
                topic.save()
                at_least_one_is_correct = False
                for choice_form in choice_formset:
                    choice = choice_form.save(commit=False)
                    at_least_one_is_correct |= choice.is_correct
                    choice.question = question
                    choice.save()
            
                if at_least_one_is_correct:
                    return redirect(topic)
                
                questionform.errors['__all__'] = questionform.error_class(['É necessário que pelo menos uma opção seja a correta. Marque a opção "É a alternativa correta?" de pelo menos uma opção'])
      
        context = {
            "question_formset": questionform_set,
            "choice_formset": choice_formset,
        }
        return render(request, "mydidata/multiple_choice_question_cru.html", context)
    else:

        question_formset = MultipleChoiceQuestionFormSet(prefix='question', queryset=Question.objects.filter(uuid=question.uuid))
        choice_formset = ChoiceFormSet(prefix='choice', queryset=Choice.objects.filter(question=question))

        context = {
            "question_formset": question_formset,
            "choice_formset": choice_formset,
        }
        return render(request, "mydidata/multiple_choice_question_cru.html", context)

@login_required()
def question_types(request, topic_uuid):
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    types = [
        ("multiple_choice", "Múltipla Escolha"),
        ("discursive", "Discursiva"),
        ("c_programming", "Programação em C")
    ]

    return render(request, "mydidata/question_types.html", {"types": types, "topic": topic})





def discipline_detail(request, uuid=None):
    return HttpResponseRedirect('/mydidata/topics?discipline=' + uuid)

def resource_room_topics(request, uuid=None, resource_room_only = None):
    r_room = get_object_or_404(ResourceRoom, uuid=uuid)
    discipline = r_room.topics.all().first().discipline
    return HttpResponseRedirect('/mydidata/topics?discipline=' + discipline.uuid + '&resource_room_only=' + resource_room_only)


def download_answers(request, topic_uuid, class_id):
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass = get_object_or_404(Classroom, pk=class_id)
    student_list = klass.students.all().order_by('first_name').order_by('last_name')
    filename = "respotas.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = "attachment; filename=\"%s\"" % filename

    writer = csv.writer(response)
    first_row = ["Alunos"] + [q.text_escaped() for q in topic.question_set.all().order_by('index')]
    rows = [first_row]
    
    for student in student_list:
        answer_row = ["%s %s"%(student.first_name, student.last_name)]
        for question in topic.question_set.all().order_by('index'):            
            answer = Answer.objects.filter(question=question, student = student).first()
            if answer:
                answer_row.append(answer.text_escaped())
        rows.append(answer_row)
    
    writer.writerows(rows)

    return response

@login_required()
def create_team(request):
    print("ENTREI NA VIEW")
    if request.POST:
        form = TeamForm(request.POST, user=request.user)
        if form.is_valid():
            team = form.save()
            team.owner = request.user
            team.members.set(form.cleaned_data['members'])
            team.save()
            redirect_url = reverse('mydidata:team_detail', args=(team.pk,))
            if request.POST.get("redirect_to", None):
                redirect_url = request.POST.get("redirect_to")
            return redirect(redirect_url)
    else:
        context = {'form': form}
        if request.GET.get("redirect_to", None):
            context["redirect_to"] = request.GET.get("redirect_to")

        form = TeamForm(initial={'owner': request.user, "members": [request.user]}, user=request.user)
    return render(request, 'mydidata/team_cru.html', context=context)

@login_required()
def team_edit(request, id):
    team = get_object_or_404(Team, pk=id)
    if request.POST:
        form = TeamForm(request.POST, instance=team, user=request.user)
        team = form.save()
        team.members.set(form.cleaned_data['members'])
        team.save()
        return redirect(reverse('mydidata:team_detail', args=(team.id, )))
    else:
        form = TeamForm(user=request.user)
    return render(request, 'mydidata/team_cru.html', {'form': form})

@login_required()
def team_list(request):
    if request.user.is_superuser:
        teams = Team.objects.all()
        return render(request, 'mydidata/team_list.html', {'teams': teams})
    teams = Team.objects.filter(owner=request.user)
    return render(request, 'mydidata/team_list.html', {'teams': teams})


@login_required()
def team_detail(request, id):
    team = get_object_or_404(Team, pk=id)
    return render(request, 'mydidata/team_detail.html', {'team': team})

@login_required()
def define_team(request):
    if not settings.ENABLE_TEAM_LINK:
        return render(request, 
                'mydidata/define_team.html', 
                {'errorMessages': ["Não é possível definir equipes no momento"],})
        
    
    if request.POST:


        index = 1;
        if not request.session.get('teams', False):
                request.session['teams'] = {}
        request.session['teams'][str(request.user.id)] = []
        
        while request.POST.get('selStudent' + str(index), False):
            studentID = request.POST['selStudent' + str(index)]
            member = User.objects.get(pk=studentID);
            if not member in request.session['teams'][str(request.user.id)]:
                request.session['teams'][str(request.user.id)].append(member.id)


            index += 1
        request.session.modified = True
        return HttpResponseRedirect(reverse('mydidata:disciplines'))
    else:
        selectedMembers = []
        if request.session.get('teams', False) and request.session['teams'].get(str(request.user.id), False):
            selectedMembers = [get_object_or_404(User, pk=student_id) for student_id in request.session['teams'][str(request.user.id)]]

        classrooms = Classroom.objects.filter(students__id = request.user.id)
        studentsToSelect = [student for classroom in classrooms for student in classroom.students.all()]
        studentsToSelect.sort(key=lambda student: student.first_name)
        return render(request, 
                'mydidata/define_team.html', 
                {'studentList': studentsToSelect, 'selectedMembers': selectedMembers,}
        )

def test_job(request, answer_id):
    answer_obj = get_object_or_404(Answer, pk=answer_id)

    return HttpResponseRedirect("/")




def get_corrections(request, answer_id):
    answer_obj = get_object_or_404(Answer, pk=answer_id)
    correct_answers.now([answer_id])
    if request.user.is_superuser:

        return feedback(request, answer_obj.id)
    else:
        return HttpResponseRedirect(answer_obj.get_detail_url())

def correct_topic(request, class_id, topic_uuid):
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass = get_object_or_404(Classroom, pk=class_id)
    
    correct_answers([a.id for a in klass.get_answers_for_topic(topic)])
    
    return HttpResponseRedirect(topic.get_absolute_url())

@csrf_exempt
def assess_answers(request):
    print("REQUEST: ", request)
    print(request.body)
    received_json = json.loads(request.body)
    
    answer_matrix = [["Students", "Question"]]
    for a in received_json["answers"]:
        answer_matrix.append([a['student'], a['text']])
    ref_answers = received_json["ref_answers"]
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

    return JsonResponse({"results": json_results})

@login_required()
def detect_copies(request, question_uuid):

    classroom = Classroom.objects.filter(students__id=request.user.id).first()
    question = get_object_or_404(Question, uuid=question_uuid)

    answers = Answer.objects.filter(question = question, student__id__in=classroom.students.all())

    [(a2, a1) for a1 in answers for a2 in answers if a1.text.replace(" ", "") == a2.text.replace(" ", "")]


    return render(request, 'mydidata/copy_detector.html', {'question': question, 'answers': [a.student for a in answers]})

@login_required()
def send_mail_to_class(request, class_id):
    classroom = get_object_or_404(Classroom, pk=class_id)
    deadlines = Deadline.objects.filter(classroom=classroom)
    localtime = timezone.localtime()
    
    t_diff = timedelta(hours=24)
    is_dst = localtime.tzinfo._dst.seconds != 0
    #veririfica se estã em horário de verão e desconta mais uma hora
    if is_dst:
        localtime -= timedelta(hours=1)
        t_diff = timedelta(hours=24 + 1)
    user = request.user
    for d in deadlines:
        local_due_date = timezone.localtime(d.due_datetime)
        if (d.due_datetime - localtime)  <= t_diff:
            topic = d.topic 
            user.email_user("AprendaFazendo: prazo para atividades em %s encerram hoje!"%topic.topic_title, "Acesse suas atividades em: https://aprendafazendo.net/%s"%topic.uuid )