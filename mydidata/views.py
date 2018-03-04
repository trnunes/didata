from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from .models import Question, Choice, DiscursiveAnswer, MultipleChoiceAnswer, Topic, Test, Discipline, Classroom
from django.template import loader
from django.http import Http404
from django.urls import reverse
import sys
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from .forms import SubscriberForm, TopicForm, QuestionForm, DiscursiveAnswerForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.conf import settings
import boto3
 
class HomePage(TemplateView):
    """
    Because our needs are so simple, all we have to do is
    assign one value; template_name. The home.html file will be created
    in the next lesson.
    """
    template_name = 'mydidata/home.html'

class TopicList(ListView):
    model = Topic
    template_name = 'mydidata/topic_list.html'
    context_object_name = 'topics'

    def get_queryset(self):
        discipline_id = self.request.GET.get('discipline', None)
        discipline = Discipline.objects.get(uuid=discipline_id)
        topic_list = Topic.objects.filter(discipline=discipline).order_by('order')
        
        return topic_list


    def dispatch(self, *args, **kwargs):
        return super(TopicList, self).dispatch(*args, **kwargs)
        
class DisciplineList(ListView):
    model = Discipline
    template_name = 'mydidata/discipline_list.html'
    context_object_name = 'disciplines'

    def get_queryset(self):



        discipline_list = Discipline.objects.order_by('name')

        return discipline_list
        

    def dispatch(self, *args, **kwargs):
        return super(DisciplineList, self).dispatch(*args, **kwargs)

def subscriber_new(request, classroom_id, template='mydidata/subscriber_new.html'):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            # Unpack form values
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data['email']
            # Create the User record
            user = User(first_name=first_name, last_name = last_name, username=username, email=email)
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

def index(request):
    question_list = Question.objects.order_by('-question_text')
    template = loader.get_template("mydidata/index.html")
    context = {
        'question_list':question_list,
    }
    return render(request, 'mydidata/index.html', context)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'mydidata/detail.html', {'question': question})

@login_required
def progress(request, discipline_name):
    
    discipline = Discipline.objects.get(name=discipline_name)
    students = discipline.students.all().order_by('first_name');
    topics = discipline.topic_set.all()
    return render(request, 'mydidata/progress.html', {'students': students, 'topics':topics,})

@login_required 
def my_progress(request):
    student = request.user
    topics = []

    
    for discipline in Discipline.objects.filter(students__id = request.user.id):
        topics.extend(discipline.topic_set.all())
    return render(request, 'mydidata/progress.html', {'students': [student], 'topics':topics,})
    
@login_required()
def discursive_answer_detail(request, answer_id):
    answer = DiscursiveAnswer.objects.get(pk=answer_id)
    return render(request, 'mydidata/discursive_answer_detail.html', {'answer':answer,})

@login_required()
def multiple_choice_answer_detail(request, answer_id):
    answer = MultipleChoiceAnswer.objects.get(pk=answer_id)
    return render(request, 'mydidata/multiple_choice_answer_detail.html', {'answer':answer,})
    
@login_required()
def discursive_answer(request, question_uuid):
    question = get_object_or_404(Question, uuid=question_uuid)
    answer = question.answer_set.filter(student=request.user).first()
    if not answer:
        answer = DiscursiveAnswer(student = request.user, question=question)
    else:
        answer = answer.discursiveanswer
        
    if request.POST:
        
        if request.FILES.get('assignment_file', False):
            file_name = request.FILES['assignment_file'].name
            request.FILES['assignment_file'].name = answer.get_answer_file_id() + "." +  file_name.split(".")[-1]
        
        answer_form = DiscursiveAnswerForm(request.POST, request.FILES, instance=answer)
        
        if answer_form.is_valid():
            answer_form.save()


            if request.session.get('teams', False):
                if request.session['teams'].get(str(request.user.id), False):

                    for member_id in request.session['teams'][str(request.user.id)]:
                        member = User.objects.get(pk=member_id)
                        member_answer = question.answer_set.filter(student=member).first()
                        
                        if not member_answer:
                            member_answer = DiscursiveAnswer()
                        else:
                            member_answer = member_answer.discursiveanswer
                            
                        member_answer.student = member
                        member_answer.question = question
                        
                        
                        member_answer.answer_text = answer.answer_text
                        member_answer.assignment_file = answer.assignment_file
                        
                        member_answer.save()
                        question.save()


                        member_answer = question.answer_set.filter(student=member).first()


                        
            return HttpResponseRedirect(reverse('mydidata:topic_detail', args=(question.topic.uuid,)))
        else:
            context = {  
                'question': question,
            }
            context['form'] = answer_form
            return render(request, 'mydidata/answer_cru.html', context) 
    else:
        context = {  
            'question': question,
        }
        
        form = DiscursiveAnswerForm(instance=answer)
        context['form'] = form
        return render(request, 'mydidata/answer_cru.html', context)
    
@login_required()
def multiple_choice_answer(request, question_uuid):
    question = get_object_or_404(Question, uuid=question_uuid)
    answer = question.answer_set.filter(student=request.user).first()
    if not answer:
        answer = MultipleChoiceAnswer(student = request.user, question=question)
    else:
        answer = answer.multiplechoiceanswer
        
    if request.POST:
        try:
            selected_choice = question.choice_set.get(pk=request.POST['choice'])
            answer.choice = selected_choice
        except (KeyError, Choice.DoesNotExist):
            context = {
                'question': question,
                'error_message': "You didn't select a choice.",
            }
            return render(request, 'mydidata/answer_cru.html', context)
        else:
            answer.save()
            return HttpResponseRedirect(reverse('mydidata:topic_detail', args=(question.topic.uuid,)))
    else:
        context = {  
            'question': question,
        }
        
        form = DiscursiveAnswerForm(instance=answer)
        context['form'] = form
        return render(request, 'mydidata/answer_cru.html', context)
        

def topic_detail(request, uuid):
    topic = Topic.objects.get(uuid=uuid)
    topic.topic_content = topic.topic_content.replace("<iframe", "<iframe allowfullscreen=\"allowfullscreen\"")
    questions = Question.objects.filter(topic=topic).order_by('index')
    context = {
        'topic': topic,
        'questions': questions,
    }
    return render(request, 'mydidata/topic_detail.html', context)
    
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
def topic_cru(request, uuid=None):

    if uuid:
        topic = get_object_or_404(Topic, uuid=uuid)
        if topic.owner != request.user:
            return HttpResponseForbidden()
    else:
        topic = Topic(owner=request.user)

    if request.POST:
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            redirect_url = reverse(
                'mydidata:topic_detail',
                args=(topic.uuid,)
            )
            return HttpResponseRedirect(redirect_url)
    else:
        form = TopicForm(instance=topic)

    variables = {
        'form': form,
        'topic':topic
    }
    if request.is_ajax():
        template = 'mydidata/topic_item_form.html'
    else:
        template = 'mydidata/topic_cru.html'

    return render(request, template, variables)
    
@login_required()
def question_detail(request, uuid):

    question = Question.objects.get(uuid=uuid)

    return render(request, 
                'mydidata/question_detail.html', 
                {'question': question}
    )
    
@login_required()
def question_cru(request, uuid=None, topic=None):
    if uuid:
        question = get_object_or_404(Question, uuid=uuid)
    else:
        question = Question()
    if request.POST:
        form = QuestionForm(request.POST, instance=question)
        
        if form.is_valid():
            # make sure the user owns the account
            topic = form.cleaned_data['topic']
            # save the data
            question = form.save(commit=False)
            question.owner = request.user
            question.save()
            # return the user to the account detail view
            reverse_url = reverse(
                'mydidata:topic_detail',
                args=(topic.uuid,)
            )
            return HttpResponseRedirect(reverse_url)
        else:
            # if the form isn't valid, still fetch the account so it can be passed to the template
            topic = form.cleaned_data['topic']
    else:
        form = QuestionForm(instance=question)
    if request.GET.get('topic', ''):
        topic = Topic.objects.get(id=request.GET.get('topic', ''))


    variables = {
        'form': form,
        'question': question,
        'topic': topic
    }

    template = 'mydidata/question_cru.html'

    return render(request, template, variables)

def discipline_detail(request, uuid=None):
    return HttpResponseRedirect('/mydidata/topics?discipline=' + uuid)

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
        print("Session data")

        print("SELECTED MEMBERS: ")
        print(selectedMembers)
        return render(request, 
                'mydidata/define_team.html', 
                {'studentList': studentsToSelect, 'selectedMembers': selectedMembers,}
        )

