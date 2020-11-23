from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from .models import Question, Choice, Topic, Test, Discipline, Classroom, ResourceRoom, Answer, TestUserRelation, Profile
from django.template import loader
from django.http import Http404
from django.urls import reverse
import sys
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from .forms import SubscriberForm, ProfileForm, UserUpdateForm, TopicForm, QuestionForm, SuperuserAnswerForm, AnswerFormUploadOnly, get_answer_form
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
from .tasks import go_academico
class HomePage(TemplateView):
    """
    Because our needs are so simple, all we have to do is
    assign one value; template_name. The home.html file will be created
    in the next lesson.
    """
    template_name = 'mydidata/home.html'


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

class TopicList(ListView):
    model = Topic
    template_name = 'mydidata/topic_list.html'
    context_object_name = 'topics'

    def get_queryset(self):
        discipline_id = self.request.GET.get('discipline', None)
        resource_room_only = self.request.GET.get('resource_room_only', False) == "True"
        discipline = Discipline.objects.get(uuid=discipline_id)
        topic_list = Topic.objects.filter(discipline=discipline, is_resource=resource_room_only, is_assessment=False).order_by('order')
        
        return topic_list
    def dispatch(self, *args, **kwargs):
        return super(TopicList, self).dispatch(*args, **kwargs)
        
class DisciplineList(ListView):
    model = Discipline
    template_name = 'mydidata/discipline_list.html'
    context_object_name = 'disciplines'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            discipline_list = []
            classrooms = Classroom.objects.filter(students__id=self.request.user.id)
            discipline_list = set([d for klass in classrooms for d in klass.disciplines.order_by('name').all()])
            
        else:
            discipline_list = discipline_list = Discipline.objects.filter(enabled=True).order_by('name')
        return discipline_list
        

    def dispatch(self, *args, **kwargs):
        return super(DisciplineList, self).dispatch(*args, **kwargs)

def academico(request):
    go_academico()

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
    print("CLASS: ", class_id)
    print("TOPIC: ", topic_uuid)
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass.closed_topics.add(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def topic_open(request, topic_uuid, class_id):
    print("CLASS: ", class_id)
    print("TOPIC: ", topic_uuid)
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

                print(a.is_ok(), " - ", a.status == Answer.CORRECT)

    return redirect('mydidata:class_progress', class_id=class_id, )

def test_close(request, uuid, class_id):
    print("CLASS: ", class_id)
    print("TOPIC: ", topic_uuid)
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass.closed_topics.add(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

def test_open(request, uuid, class_id):
    print("CLASS: ", class_id)
    print("TOPIC: ", topic_uuid)
    klass = get_object_or_404(Classroom, pk=class_id)
    topic = get_object_or_404(Topic, uuid=topic_uuid)
    klass.closed_topics.remove(topic)
    klass.save()

    return redirect('mydidata:class_progress', class_id=class_id, )

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
def my_progress(request):
    student = request.user
    topics = []
    d = Discipline.objects.filter(students__id = request.user.id)
    print("Disciplines: ", d)
    for discipline in Discipline.objects.filter(students__id = request.user.id):
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
def calculate_grades(request, class_id, topic_uuid=None):
    classroom = get_object_or_404(Classroom, pk=class_id)
    if topic_uuid:
        topics = [get_object_or_404(Topic, uuid=topic_uuid)]
    else:
        discipline = classroom.disciplines.all().first()
        topics = classroom.closed_topics.all()
    
    student_list = classroom.students.all().order_by('first_name')    
    student_by_topic_grade = {}
    for student in student_list:
        student_by_topic_grade[student] = []
        sum_topic_weight = 0
        final_grade = 0

        for topic in topics:
            sum_grades = 0
            sum_weights = 0
            sum_topic_weight += topic.weight

            for q in topic.question_set.all():
                answer = Answer.objects.filter(student=student, question=q).first()
                if answer: sum_grades += answer.grade * q.weight
                sum_weights += q.weight
            wavg = 0
            if sum_weights: wavg = sum_grades/sum_weights
            final_grade += wavg * topic.weight
            student_by_topic_grade[student].append([topic,  "{:2.1f}".format(wavg*10)])
        if sum_topic_weight: student_by_topic_grade[student].insert(0,["Nota", "{:2.1f}".format((final_grade/sum_topic_weight)*10)])

       
    return render(request, 'mydidata/percentage_progress.html', {'topics': topics, 'topic_dict': student_by_topic_grade})

@login_required
def answer(request, question_uuid, test_id=None):

    question = get_object_or_404(Question, uuid=question_uuid)

    if request.user.is_authenticated:
        classrooms = Classroom.objects.filter(students__id = request.user.id)
        for klass in classrooms:
            closed_topics = klass.closed_topics.all()
            if question.topic in closed_topics:
                return redirect(question.topic.get_absolute_url())

    if request.POST:        
        print("POST Question UUID: ", question_uuid)        
        if not request.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
                #TODO insert test logic here
        answer = Answer.find(student=request.user, question=question, test_id=test_id)
        form = get_answer_form(request.POST, request.FILES, instance=answer, question=question)
        answer = form.instance
        answer.question = question
        answer.student = request.user
        answer.status = Answer.SENT
        
        if test_id:
            test = get_object_or_404(Test, pk=test_id)
            tuserrelation = TestUserRelation.objects.filter(test=test,student=request.user).first()
            if tuserrelation.is_closed:
                context = {
                    'question': question,            
                    'form': form,
                    'error_message': "Esta avaliação esta finalizada. Já não é possível enviar respostas."
                }
                return render(request, 'mydidata/answer_cru.html', context)


            answer.test = test
            redirect_url = question.get_next_answer_url(request.user, test)
            if not redirect_url:
                
                tuserrelation.is_closed = True
                tuserrelation.save()
                redirect_url = reverse('mydidata:test_progress', args=(test.uuid,))
        else:
            redirect_url = question.next_question_url()
        
        if request.FILES.get('assignment_file', False):
            file_name = request.FILES['assignment_file'].name
            request.FILES['assignment_file'].name = answer.get_answer_file_id() + "." +  file_name.split(".")[-1]
        
        if form.is_valid():
            form.save()

            #TODO insert logic for team work

        else:
            print("FORM ERROR: ")
            context = {
                'question': question,            
                'form': form,
            }
            return render(request, 'mydidata/answer_cru.html', context)
        print("REDIRECT URL: ", redirect_url)
        return HttpResponseRedirect(redirect_url)


    form = get_answer_form(question=question)
    if request.user.is_authenticated:
        answer = Answer.find(student=request.user, question=question, test_id=test_id)
        if answer:
            print("Answer found: ", answer.answer_text, answer.assignment_file)
        else:
            print("Answer not found")
        form = get_answer_form(instance=answer, question=question)

    context = {
        'question': question,        
        'form': form,
    }
    print("GET: ", question.uuid)
    return render(request, 'mydidata/answer_cru.html', context)



def discursive_answer_detail(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)

    return render(request, 'mydidata/discursive_answer_detail.html', {'answer': answer, })

@login_required()
def multiple_choice_answer_detail(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)
    return render(request, 'mydidata/multiple_choice_answer_detail.html', {'answer':answer,})

@login_required()
def feedback(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question
    form = SuperuserAnswerForm(instance=answer)
    classroom = Classroom.objects.filter(students__id=answer.student.id).first()

    if request.POST:
        form = SuperuserAnswerForm(request.POST, instance=answer)

        form.save()
        
        students = classroom.students.all().order_by('first_name');

        next_student_found = False
        student_index = 1

        for student in students:
            if next_student_found:
                next_answer = Answer.objects.filter(student=student, question=question).first()
                if next_answer:
                    form = SuperuserAnswerForm(instance=next_answer)
                    context = {
                        'question': question,
                        'form': form,
                        'answer': next_answer,
                        'classroom': classroom,
                        'action_url': reverse('mydidata:feedback', args=(next_answer.id,)),
                    }
                    return render(request, 'mydidata/answer_cru.html', context)

            if student.id == answer.student.id and student_index < students.count(): next_student_found = True
            student_index += 1

        return redirect('mydidata:class_progress', class_id=classroom.id)


    context = {
        'question': question,
        'form': form,
        'action_url': reverse('mydidata:feedback', args=(answer_id,)),
    }
    return render(request, 'mydidata/answer_cru.html', context)

@login_required()
def multiple_choice_answer(request, question_uuid, test_id = None):
    #TODO remove duplicated code with #discursive_answer
    question = get_object_or_404(Question, uuid=question_uuid)
    test = None
    if test_id:    
        test = get_object_or_404(Test, pk=test_id)
        answer = question.answer_set.filter(student=request.user, test=test_id).first()
    else:
        answer = question.answer_set.filter(student=request.user).first()

    if not answer:
        answer = Answer(student = request.user, question=question)
        if test:
            answer.test = test
    else:
        answer = answer.multiplechoiceanswer

    if request.POST:
        
        if test:
            classroom = Classroom.objects.filter(students__id=request.user.id).first()
            tuserrelation = TestUserRelation.objects.filter(test=test,student=request.user).first()
            closed_for_student = (tuserrelation and tuserrelation.is_closed)
            if test in classroom.closed_tests.all() or closed_for_student:
                context = {
                    'question': question,
                    'answer': answer,
                    'test': test,
                    'error_message': 'Não é possível cadastrar questões para avaliações fechadas!'
                }
                return render(request, 'mydidata/answer_cru.html', context)

        try:
            selected_choice = question.choice_set.get(pk=request.POST['choice'])
            answer.choice = selected_choice
            answer.status = Answer.SENT
        except (KeyError, Choice.DoesNotExist):
            context = {
                'test': test,
                'question': question,
                'error_message': "You didn't select a choice.",
            }
            return render(request, 'mydidata/answer_cru.html', context)
        else:
            answer.save()
            if request.session.get('teams', False):
                if request.session['teams'].get(str(request.user.id), False):

                    for member_id in request.session['teams'][str(request.user.id)]:
                        member = User.objects.get(pk=member_id)
                        member_answer = question.answer_set.filter(student=member).first()
                        
                        if not member_answer:
                            member_answer = Answer()
                        else:
                            member_answer = member_answer.multiplechoiceanswer
                            
                        if test:
                            member_answer.test = test

                        member_answer.student = member
                        member_answer.question = question
                        
                        member_answer.choice = answer.choice

                        member_answer.save()
                        question.save()
                        member_answer = question.answer_set.filter(student=member).first()

            if test:
                redirect_url = question.get_next_answer_url(request.user, test)
                if not redirect_url:
                    tuserrelation.is_closed = True
                    tuserrelation.save()
                    redirect_url = reverse('mydidata:test_progress', args=(test.uuid,))
            else:
                redirect_url = reverse('mydidata:topic_detail', args=(question.topic.uuid,))

            return HttpResponseRedirect(redirect_url)
    else:
        context = {
            'question': question,
            'answer': answer,
        }
        if test: context['test']=test
        return render(request, 'mydidata/answer_cru.html', context)


def discursive_answer(request, question_uuid, test_id = None):
    return answer(request, question_uuid, test_id)
    question = get_object_or_404(Question, uuid=question_uuid)
    test = None
    answer = None
    if test_id: test = get_object_or_404(Test, pk=test_id)
    if not request.user.is_authenticated:
        if request.POST:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
        else:
            context = {
                'question': question,
                'test': test,
                'error_message': 'Você precisa fazer o login para responder!'
            }

        return render(request, 'mydidata/answer_cru.html', context)
    
    if test_id:        
        answer = question.answer_set.filter(student=request.user, test=test_id).first()
    else:
        answer = question.answer_set.filter(student=request.user).first()
   
    if not answer:
        answer = Answer(student = request.user, question=question)        
        if test:
            answer.test = test
    else:
        answer.status = Answer.SENT
    
    if request.POST:
        if not request.user.is_authenticated: return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

        if test:
            classroom = Classroom.objects.filter(students__id=request.user.id).first()
            tuserrelation = TestUserRelation.objects.filter(test=test,student=request.user).first()
            closed_for_student = (tuserrelation and tuserrelation.is_closed)
            if test in classroom.closed_tests.all() or closed_for_student:
                context = {
                    'question': question,
                    'test': test,
                    'error_message': 'Não é possível cadastrar questões para avaliações fechadas!'
                }
                return render(request, 'mydidata/answer_cru.html', context)

        
        if request.FILES.get('assignment_file', False):
            file_name = request.FILES['assignment_file'].name
            request.FILES['assignment_file'].name = answer.get_answer_file_id() + "." +  file_name.split(".")[-1]
        
        answer_form = AnswerForm(request.POST, request.FILES, instance=answer)
        if answer_form.is_valid():
            
            answer_form.save()            

            if request.session.get('teams', False):
                if request.session['teams'].get(str(request.user.id), False):

                    for member_id in request.session['teams'][str(request.user.id)]:
                        member = User.objects.get(pk=member_id)
                        member_answer = question.answer_set.filter(student=member).first()
                        
                        if not member_answer:
                            member_answer = Answer()
                        else:
                            member_answer = member_answer.discursiveanswer
                        if test:
                            member_answer.test = test

                        member_answer.student = member
                        member_answer.question = question
                        
                        
                        member_answer.answer_text = answer.answer_text
                        member_answer.assignment_file = answer.assignment_file
                        
                        member_answer.save()
                        question.save()

                        member_answer = question.answer_set.filter(student=member).first()
            if test_id:
                redirect_url = reverse('mydidata:test_detail', args=(test.uuid,))
            else:
                redirect_url = reverse('mydidata:topic_detail', args=(question.topic.uuid,))

            return HttpResponseRedirect(redirect_url)
        else:            
            context = {
                'question': question,
                'answer': answer,
                'form': answer_form,
            }
            if test: context['test'] = test;


        return render(request, 'mydidata/answer_cru.html', context)
            
    else:
        form = AnswerForm(instance=answer)
        context = {
            'question': question,
            'answer': answer,
            'form': form,
        }
        if test: context['test'] = test;


        return render(request, 'mydidata/answer_cru.html', context)


@login_required()
def test_progress(request, uuid, class_id=None):
    test = get_object_or_404(Test, uuid=uuid)
    students = [request.user]
    classroom = None
    if class_id:
        classroom = Classroom.objects.filter(pk=class_id).first()

    if request.user.is_superuser and class_id:
        students = classroom.students.all().order_by('first_name')

    student_grade = {}
    assessment = {}    
    for student in students:
        test_user = TestUserRelation.objects.filter(test=test, student=student).first()
        total_weight = 0
        sum_weights = 0
        final_grade = 0
        student_grade[student] = {}
        if test_user:
            for q in test_user.current_questions():
                answer = Answer.objects.filter(student=student, question=q, test=test).first()
                if answer:
                    answer.correct()        
                    sum_weights += answer.grade * q.weight
                total_weight += q.weight
            final_grade = 0
            if sum_weights: final_grade = (sum_weights/total_weight) * 10
            
            student_grade[student]['grade'] = "{:2.1f}".format(final_grade)
            student_grade[student]['test_user'] = test_user
            if final_grade < 6:
                assessment['fail'] = "Infelizmente você não atingiu a nota mínima necessária."
                if test_user.has_next_try():
                    assessment['next_try_link'] = reverse('mydidata:next_try', args=(test_user.id,))
            else:
                assessment['success'] = "Parabéns, você concluiu com sucesso esta avaliação!"
        else:
            student_grade[student]['grade'] = '?'

    return render(request, 'mydidata/test_progress.html', {'classroom':classroom, 'students': students, 'test':test, 'student_grades': student_grade, 'assessment':assessment,})

@login_required()
def next_try(request, test_user_id):
    test_user_rel = get_object_or_404(TestUserRelation, pk=test_user_id)
    return HttpResponseRedirect(test_user_rel.next_try())
    
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
            test_user_relation.generate_question_index()
            test_user_relation.save()
    context = {
        'topic': topic,
        'questions': questions,
        'test_user_relation': test_user_relation
    }

    if topic.has_assessment_question and questions and request.user.is_authenticated:
        context['question'] = questions[0]
        questions = questions[1:]
    
    return render(request, 'mydidata/topic_detail.html', context)

@login_required
def start_test(request, uuid):
    test = get_object_or_404(Test, uuid=uuid)
    test_user = TestUserRelation.objects.filter(student=request.user, test=test).first()
    if not test_user:
        test_user = TestUserRelation.objects.create(student=request.user, test=test)
        test_user.generate_question_index()
        test_user.save()

    first_question = test_user.current_questions()[0]
    return HttpResponseRedirect(first_question.get_answer_url(test))

    
@login_required
def test_detail(request, uuid):
    test = get_object_or_404(Test, uuid=uuid)

    classroom = Classroom.objects.filter(students__id=request.user.id).first()    
    questions = list(test.questions.order_by('index').all())

    print("Questions: ", len(questions))

    tu = TestUserRelation.objects.filter(student=request.user, test=test).first()
    
    if (not tu):
        import random
        tu = TestUserRelation.objects.create(student=request.user, test=test)
        tu.generate_question_index()
        tu.save()

    print("SIZE", tu.index_list_as_array())
    reordered_questions = [questions[i-1] for i in tu.index_list_as_array()]

    context = {
        'questions': reordered_questions,
        'classroom': classroom,
        'test': test,

    }
    
    if reordered_questions and not tu.is_closed:
        first_question = reordered_questions[0]
        return HttpResponseRedirect(first_question.get_answer_url(test))
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
    print("MY QUESTION", question.question_text)
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))', question.question_text)
    for url in urls:
        if url.find("upload"):
            new_url = settings.UPLOAD_URL + "/uploads/" + url.split("uploads")[-1]
            question.question_text = question.question_text.replace(url, new_url)

    return render(request, 
                'mydidata/question_detail.html', 
                {'question': question}
    )
    
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
        print("Session data")

        print("SELECTED MEMBERS: ")
        print(selectedMembers)
        return render(request, 
                'mydidata/define_team.html', 
                {'studentList': studentsToSelect, 'selectedMembers': selectedMembers,}
        )
@login_required()
def detect_copies(request, question_uuid):

    classroom = Classroom.objects.filter(students__id=request.user.id).first()
    question = get_object_or_404(Question, uuid=question_uuid)

    answers = Answer.objects.filter(question = question, student__id__in=classroom.students.all())

    [(a2, a1) for a1 in answers for a2 in answers if a1.text.replace(" ", "") == a2.text.replace(" ", "")]


    return render(request, 'mydidata/copy_detector.html', {'question': question, 'answers': [a.student for a in answers]})