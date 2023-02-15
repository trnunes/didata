from venv import create
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, Client
from mydidata.models import Classroom, ContentVersion, Answer, Test, Topic, TestUserRelation, Question, Choice, Discipline, Team
from mydidata.forms import TeamForm, TopicForm, ContentVersionForm, AnswerForm
from mydidata.tasks import detect_copies
from http import HTTPStatus
from django.core.management import call_command



# class UsersManagersTests(TestCase):
    # def test_create_user(self):
        # User = get_user_model()
        # user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        # self.assertEqual(user.email, 'normal@user.com')
        # self.assertTrue(user.is_active)
        # self.assertFalse(user.is_staff)
        # self.assertFalse(user.is_superuser)
        # try:
            # self.assertIsNone(user.username)
        # except AttributeError:
            # pass
        # with self.assertRaises(TypeError):
            # User.objects.create_user()
        # with self.assertRaises(TypeError):
            # User.objects.create_user(email='')
        # with self.assertRaises(ValueError):
            # User.objects.create_user(email='', password="foo")
    # 
    # def test_create_superuser(self):
        # User = get_user_model()
        # admin_user = User.objects.create_superuser(email='super@user.com', password='pass', username="foo")
        # self.assertEqual(admin_user.email, 'super@user.com')
        # self.assertTrue(admin_user.is_active)
        # self.assertTrue(admin_user.is_staff)
        # self.assertTrue(admin_user.is_superuser)
# 
        # try:
            # self.assertIsNone(admin_user.username)
        # except AttributeError:
            # pass
        # with self.assertRaises(ValueError):
            # User.objects.create_superuser(
                # email='super@user.com', password="foo", is_superuser = False)
class TeamTests(TestCase):
    def test_create_team(self):
        student1 = User.objects.create(username="std1", password="baa", first_name='Student', last_name='One')
        student1.set_password("baa")
        student1.save()
        student2 = User.objects.create(username="std2", password="baa", first_name='Student', last_name='Two')
        student2.set_password("baa")
        student2.save()
        student3 = User.objects.create(username="std3", password="baa", first_name='Student', last_name='Three')
        student3.set_password("baa")
        student3.save()
        form_data = {
            'name': 'Test Team',
            'owner': student1.pk,
            'members': [student1.pk, student2.pk, student3.pk]
        }
        self.client.login(username='std1', password='baa')  
        form = TeamForm(data=form_data, user=student1)
        self.assertTrue(form.is_valid())
        team = form.save()
        self.assertEqual(team.name, 'Test Team')
        self.assertEqual(set(team.members.all()), set([student1, student2, student3]))
        

    def test_create_team_view(self):
        client = Client()
        student1 = User.objects.create(username="std1", password="baa", first_name='Student', last_name='One')
        student1.set_password("baa")
        student1.save()
        student2 = User.objects.create(username="std2", password="baa", first_name='Student', last_name='Two')
        student2.set_password("baa")
        student2.save()
        student3 = User.objects.create(username="std3", password="baa", first_name='Student', last_name='Three')
        student3.set_password("baa")
        student3.save()
        form_data = {
            'name': 'Test Team',
            'owner': student1.pk,
            'members': [student1.pk, student2.pk, student3.pk]
        }
        client.login(username='std1', password='baa')
        response = client.post('/mydidata/teams/create/', data=form_data)
        print(response)
        self.assertEqual(response.status_code, 302)  # Check that the view returns a redirect
        self.assertEqual(Team.objects.count(), 1)  # Check that a new Team instance was created
        team = Team.objects.first()
        self.assertEqual(team.name, 'Test Team')
        self.assertEqual(set(team.members.all()), set([student1, student2, student3]))

    def test_edit_team_view(self):
        client = Client()
        student1 = User.objects.create(username="std1", password="baa", first_name='Student', last_name='One')
        student1.set_password("baa")
        student1.save()
        student2 = User.objects.create(username="std2", password="baa", first_name='Student', last_name='Two')
        student2.set_password("baa")
        student2.save()
        student3 = User.objects.create(username="std3", password="baa", first_name='Student', last_name='Three')
        student3.set_password("baa")
        student3.save()

        team = Team.objects.create(name="test team", owner=student1)
        team.members.set([student1, student2])
        form_data = {
            'name': 'Test Team Edited',
            'owner': student1.pk,
            'members': [student1.pk, student2.pk, student3.pk]
        }
        client.login(username='std1', password='baa')
        response = client.post('/mydidata/teams/edit/%d/'%team.id, data=form_data)
        print(response)
        self.assertEqual(response.status_code, 302)  # Check that the view returns a redirect
        self.assertEqual(Team.objects.count(), 1)  # Check that a new Team instance was created
        team = Team.objects.first()
        self.assertEqual(team.name, 'Test Team Edited') 
        self.assertEqual(set(team.members.all()), set([student1, student2, student3]))
    
    def test_teams_list(self):
        client = Client()
        student1 = User.objects.create(username="std1", password="baa", first_name='Student1', last_name='One')
        student1.set_password("baa")
        student1.save()
        student2 = User.objects.create(username="std2", password="baa", first_name='Student2', last_name='Two')
        student2.set_password("baa")
        student2.save()
        student3 = User.objects.create(username="std3", password="baa", first_name='Student3', last_name='Three')
        student3.set_password("baa")
        student3.save()
        student4 = User.objects.create(username="std4", password="baa", first_name='Student4', last_name='Three')
        student4.set_password("baa")
        student4.save()
        
        team = Team.objects.create(name="test team", owner=student1)
        team.members.set([student1, student2])
        
        team.save()

        team = Team.objects.create(name="test team 2", owner=student2)
        team.members.set([student3, student4])
        team.save()
        
        team = Team.objects.create(name="test team 3", owner=student2)
        team.members.set([student3, student4])
        team.save()

        client.login(username='std1', password='baa')

        response = client.get('/mydidata/teams/list/')
        self.assertContains(response, "test team")
        self.assertNotContains(response, "test team 2")
        self.assertNotContains(response, "test team 3")

    def test_teams_list_superuser(self):
        client = Client()
        student1 = User.objects.create_superuser(email="user@super.com", username="std1", password="baa", first_name='Student1', last_name='One')
        student1.set_password("baa")
        student1.save()
        student2 = User.objects.create(username="std2", password="baa", first_name='Student2', last_name='Two')
        student2.set_password("baa")
        student2.save()
        student3 = User.objects.create(username="std3", password="baa", first_name='Student3', last_name='Three')
        student3.set_password("baa")
        student3.save()
        student4 = User.objects.create(username="std4", password="baa", first_name='Student4', last_name='Three')
        student4.set_password("baa")
        student4.save()
        
        team = Team.objects.create(name="test team", owner=student1)
        team.members.set([student1, student2])
        
        team.save()

        team = Team.objects.create(name="test team 2", owner=student2)
        team.members.set([student3, student4])
        team.save()
        
        team = Team.objects.create(name="test team 3", owner=student2)
        team.members.set([student3, student4])
        team.save()

        client.login(username='std1', password='baa')

        response = client.get('/mydidata/teams/list/')
        self.assertContains(response, "test team")
        self.assertContains(response, "test team 2")
        self.assertContains(response, "test team 3")

class AnswerTests(TestCase):

    def setUp(self):
        call_command('collectstatic', verbosity=0, interactive=False)
    
    def test_answer_form_discursive(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        created_test.save()

        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user, test=created_test)
        self.assertTrue(answerForm.is_valid())
        answerForm.save()

        answerInDB = Answer.objects.filter(student=user,question=q1,test=created_test).first()

        self.assertEqual("resposta da questão 1", answerInDB.answer_text)
        self.assertEqual(answerInDB.student, user)
        self.assertEqual(answerInDB.question, q1)
        self.assertEqual(answerInDB.test, created_test)
    
        
    def test_answer_form_save_twice(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user, test=created_test)
        
        self.assertTrue(answerForm.is_valid())
        answerForm.save()
        answersInDB = Answer.objects.filter(student=user,question=q1,test=created_test)
        self.assertEqual(1, len(answersInDB))
        
        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user, test=created_test)
        self.assertTrue(answerForm.is_valid())
        answerForm.save()
        answersInDB = Answer.objects.filter(student=user,question=q1,test=created_test)
        self.assertEqual(1, len(answersInDB))
    
    def test_answer_form_multiplechoice(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        c1 = q1.choices.create(choice_text = "choice 1")
        c2 = q1.choices.create(choice_text = "choice 2")
        c3 = q1.choices.create(choice_text = "choice 3")
        c4 = q1.choices.create(choice_text = "choice 4")
        created_test.save()

        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1", "choice": c1.id}, question=q1, user=user, test=created_test)
        self.assertTrue(answerForm.is_valid())
        answerForm.save()

        answerInDB = Answer.objects.filter(student=user,question=q1,test=created_test).first()
        self.assertEqual(answerInDB.choice, c1)
        self.assertEqual(answerInDB.student, user)
        self.assertEqual(answerInDB.question, q1)
        self.assertEqual(answerInDB.test, created_test)

    def test_answer_form(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        q1 = Question.objects.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user)
        self.assertTrue(answerForm.is_valid())
        saved_answer = answerForm.save()
        
        answerInDB = Answer.objects.get(student=user,question=q1)
        self.assertEqual(saved_answer, answerInDB)

    def test_answer_form_save_twice(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        q1 = Question.objects.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user)
        self.assertTrue(answerForm.is_valid())
        answerForm.save()
        answerInDB = Answer.objects.filter(student=user,question=q1)
        self.assertEqual(1, len(answerInDB))
        
        answerForm = AnswerForm(data={"answer_text": "resposta da questão 1"}, question=q1, user=user)
        self.assertTrue(answerForm.is_valid())
        answerForm.save()
        answerInDB = Answer.objects.filter(student=user,question=q1)
        self.assertEqual(1, len(answerInDB))
    
    def test_discursive_question_view(self):
        client = Client()
        user = User.objects.create_superuser(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)

        response = client.login(username='baa', password="foo")
        
        
        response = client.get("/mydidata/discursive_question/"+ topic.uuid + "/")
        print(response)
        self.assertEqual(200, response.status_code)

    def test_discursive_question_view_post(self):
        client = Client()
        user = User.objects.create_superuser(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)

        response = client.login(username='baa', password="foo")

        data = {
            'question_text': 'What is the meaning of life?',
            'difficulty_level': 1,
            'question_type': 2,
            'weight': 1,
            'ref_keywords': 'meaning of life',
            'punish_copies': True,
        }

        # send the POST request to the view and store the response
        response = client.post("/mydidata/discursive_question/"+ topic.uuid + "/", data=data)

        print(response)

        questions = Question.objects.filter(question_text='What is the meaning of life?')
        saved_question = questions.first()
        self.assertEqual(questions.count(), 1)
        self.assertEqual(1, saved_question.difficulty_level)
        self.assertEqual(2, saved_question.question_type)
        self.assertEqual('meaning of life', saved_question.ref_keywords)
        self.assertTrue(saved_question.punish_copies)
        self.assertEqual(302, response.status_code)

    def test_discursive_question_view_post_required_data(self):
        client = Client()
        user = User.objects.create_superuser(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)

        response = client.login(username='baa', password="foo")

        data = {
            'question_text': '',
            'difficulty_level': 1,
            'question_type': 2,
            'weight': 1,
            'ref_keywords': 'meaning of life',
            'punish_copies': True,
            'invalid_field': "invalid data"
        }

        # send the POST request to the view and store the response
        response = client.post("/mydidata/discursive_question/"+ topic.uuid + "/", data=data)

        print(response)
        print(response.content)
        self.assertEqual(200, response.status_code)
        questions = Question.objects.all()
        self.assertEqual(questions.count(), 0)

        self.assertContains(response, "Este campo é obrigatório.")

class TopicCommentTests(TestCase):

    def test_create_comment(self):
        user1 = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)

        self.client.login(username="baa", password="foo")


        response = self.client.get("/mydidata/comment/create/"+str(topic.id)+"/")

        self.assertEqual(response.status_code, 200)


    def test_update_comment(self):
        pass

    def test_delete_comment(self):
        pass

    

    
class AnswerIntegrationTests(TestCase):
    
    def test_send_answer_for_team_questions_without_team(self):
        user1 = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        
        q1 = Question.objects.create(question_text= "question 1", difficulty_level = 1, question_type=3, is_team_work = True)
        q1.topic = topic
        q1.save()
        
        self.client.login(username="baa", password="foo")
        data = {"answer_text": "resposta da questão 1"}
        response = self.client.post('/mydidata/discursive_answer/%s/'%(q1.uuid,), data=data)
        answers = Answer.objects.all()
        
        self.assertEqual(answers.count(), 0)
        msg = """Você também pode pedir para participar de alguma equipe dos seus colegas ;-)"""
        self.assertContains(response, msg )
    
    def test_send_answer_for_team_question(self):
        user1 = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal2@user.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        team1 = Team.objects.create(name="Winners", owner=user1)
        team1.members.add(user1)
        team1.members.add(user2)
        team1.save()

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)

        q1 = Question.objects.create(question_text= "question 1", difficulty_level = 1, question_type=3, is_team_work = True)
        q1.topic = topic
        q1.save()

        self.client.login(username="baa", password="foo")
        data = {"answer_text": "resposta da questão 1", "team": team1.id}
        response = self.client.post('/mydidata/discursive_answer/%s/'%(q1.uuid,), data=data)
        answers = Answer.objects.all()

        self.assertEqual(answers.count(), 1)
        self.assertEqual(list(team1.answers.all()), list(answers))
        self.assertEqual(302, response.status_code )

    def test_send_answer_for_team_question_twice(self):
        user1 = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal2@user.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        team1 = Team.objects.create(name="Winners", owner=user1)
        team1.members.add(user1)
        team1.members.add(user2)
        team1.save()

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)

        q1 = Question.objects.create(question_text= "question 1", difficulty_level = 1, question_type=3, is_team_work = True)
        q1.topic = topic
        q1.save()

        self.client.login(username="baa", password="foo")
        data = {"answer_text": "resposta da questão 1", "team": team1.id}
        response = self.client.post('/mydidata/discursive_answer/%s/'%(q1.uuid,), data=data)
        response = self.client.post('/mydidata/discursive_answer/%s/'%(q1.uuid,), data=data)
        answers = Answer.objects.all()

        self.assertEqual(answers.count(), 1)
        self.assertEqual(list(team1.answers.all()), list(answers))
        self.assertEqual(302, response.status_code )

class TestUserRelationTests(TestCase):
    
    def test_generate_question_index(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        created_test.questions.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        created_test.questions.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)
        created_test.save()
        
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        first_list_index = tu.index_list_as_array()
        
        self.assertEqual(4, len(first_list_index))

        second_list_index = tu.generate_question_index()
        
        self.assertFalse(first_list_index == second_list_index)
        tu.save()
    
    def test_current_questions(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 3", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 4", uuid="4", difficulty_level = 1, question_type=3)
        created_test.save()
        
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[3,2,1,4]"
        self.assertListEqual(tu.current_questions(), [q3,q2,q1,q4])
        self.assertListEqual(tu.current_questions(), [q3,q2,q1,q4])
        self.assertListEqual(tu.current_questions(), [q3,q2,q1,q4])
        tu.save()
    
    def test_current_non_answerd_questions(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 3", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 4", uuid="4", difficulty_level = 1, question_type=3)
        created_test.save()

        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[3,2,1,4]"
        self.assertListEqual(tu.current_non_answered_questions(), [q3,q2,q1,q4])
        
        Answer.objects.create(answer_text="answer question 1", question=q1, test=created_test, student=user)
        
        self.assertListEqual(tu.current_non_answered_questions(), [q3,q2,q4])
        



    
    def test_next_non_answer_question(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 3", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 4", uuid="4", difficulty_level = 1, question_type=3)
        created_test.save()
        

        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[3,2,1,4]"
        tu.save()
        Answer.objects.create(answer_text="answer question 1", question=q2, test=created_test, student=user)
        Answer.objects.create(answer_text="answer question 1", question=q1, test=created_test, student=user)
        
        self.assertEqual(q4, tu.get_next_question(q3))
        
        self.assertIsNone(tu.get_next_question(q4))
        
    def test_next_question_without_answers(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 3", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 4", uuid="4", difficulty_level = 1, question_type=3)
        created_test.save()


        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[3,2,1,4]"
        tu.save()


        self.assertEqual(q2, tu.get_next_question(q3))

        self.assertEqual(q1, tu.get_next_question(q2))

        self.assertEqual(q4, tu.get_next_question(q1))

        self.assertIsNone(tu.get_next_question(q4))


class TestsManagementTests(TestCase):
    def test_get_or_create_test_user_relation(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        
        self.assertFalse(TestUserRelation.objects.filter(student=user, test=created_test))

        self.assertTrue(created_test.get_or_create_test_user_relation(user))
        
        self.assertTrue(TestUserRelation.objects.filter(student=user, test=created_test))

    def test_close_test_for_student(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        
        self.assertFalse(TestUserRelation.objects.filter(student=user, test=created_test))
        created_test.close_for(user)
        test_user_query_set = TestUserRelation.objects.filter(student=user, test=created_test)
        self.assertTrue(test_user_query_set)
        self.assertTrue(test_user_query_set.first().is_closed)

    def test_next_question_for_user(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[0,1]"
        tu.save()
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.assertFalse(created_test.next_question(user, question_2))
        self.assertEqual(created_test.next_question(user, question_1), question_2)
        tu.is_closed = True
        tu.save()
        self.assertFalse(created_test.next_question(user, question_1))
    
    def test_get_answers(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user2 = User.objects.create_user(email='normal2@user.com', username='baa2', password='foo2')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[0,1]"
        tu.save()
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.assertFalse(created_test.get_answers(user))
        answer1 = Answer.objects.create(answer_text="answer question 1", question=question_1, test=created_test, student=user)
        answer2 = Answer.objects.create(answer_text="answer question 2", question=question_2, test=created_test, student=user)
        self.assertAlmostEquals(list(created_test.get_answers(user)), [answer1, answer2])
        self.assertFalse(created_test.get_answers(user2))
        
    def test_next_try(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[0,1]"
        tu.save()
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.assertFalse(created_test.get_answers(user))
        answer1 = Answer.objects.create(answer_text="answer question 1", question=question_1, test=created_test, student=user)
        answer2 = Answer.objects.create(answer_text="answer question 2", question=question_2, test=created_test, student=user)
        
        answers = Answer.objects.filter(student=user, question__id__in=[question_1.id, question_2.id], test=created_test)
        self.assertAlmostEquals(list(answers), [answer1, answer2])
        created_test.next_try(user)
        tu = TestUserRelation.objects.get(student=user, test=created_test)
        self.assertEqual(tu.tries, 2)
        answers = Answer.objects.filter(student=user, question__id__in=[question_1.id, question_2.id], test=created_test)        
        self.assertFalse(answers)

    def test_next_try_exceed_limit(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        
        created_test = Test.objects.create(title="My Test", topic=topic)
        
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)

        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[0,1]"
        tu.save()
        created_test.next_try(user)

        tu = TestUserRelation.objects.get(student=user, test=created_test)
        self.assertEqual(tu.tries, 2)
        with self.assertRaises(Exception):
               created_test.next_try(user)
    
    def test_has_next_try(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user2 = User.objects.create_user(email='normal2@user.com', username='baa2', password='foo2')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        tu = TestUserRelation.objects.create(student=user, test=created_test)
        tu.index_list = "[0,1]"
        tu.save()
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.assertTrue(created_test.has_next_try(user))
        

    def test_is_closed(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        self.assertFalse(created_test.is_closed_for(user))


class TestIntegrationTests(TestCase):
    def test_start_test(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user.set_password("foo")
        user.save()
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", uuid="1", difficulty_level = 1, question_type=3)
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.client.login(username='baa', password='foo')
        response = self.client.get('/mydidata/start_test/%s/'%created_test.uuid)
        self.assertEqual(302, response.status_code)
        self.assertEqual(TestUserRelation.objects.count(), 1)
    
    def test_send_response_twice_error(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        user.set_password("foo")
        user.save()
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        question_1 = Question.objects.create(question_text= "question 1", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", difficulty_level = 1, question_type=3)
        question_1.tests.add(created_test)
        question_2.tests.add(created_test)
        self.client.login(username='baa', password='foo')

        data = {"answer_text": "resposta da questão 1"}
        response = self.client.post('/mydidata/test_answer/%s/%s/'%(question_1.uuid, created_test.id,), data=data)

        self.assertEqual(302, response.status_code)
        self.assertEqual(Answer.objects.filter(question=question_1, student=user).count(), 1)
        answer = Answer.objects.filter(question=question_1, student=user).first()
        self.assertEqual(answer.answer_text, "resposta da questão 1")
        
        data = {"answer_text": "resposta da questão 1 editada"}
        response = self.client.post('/mydidata/test_answer/%s/%s/'%(question_1.uuid, created_test.id,), data=data)
        
        answer = Answer.objects.filter(question=question_1, student=user).first()
        self.assertEqual(answer.answer_text, "resposta da questão 1")

        self.assertContains(response, "Siga para a próxima questão.")
    
    def test_progress_view(self):
        superuser = User.objects.create_superuser(email='normal@superuser1.com', username='superbaa', password='foo')
        superuser.set_password("foo")
        superuser.save()

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo', first_name="User1", last_name="Baa")
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo', first_name="User2", last_name="Baa")
        user2.set_password("foo")
        user2.save()

        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        created_test = Test.objects.create(title="My Test", topic=topic)

        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)

        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1, test=created_test)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1, test=created_test)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1, test=created_test)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1, test=created_test)

        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2, test=created_test)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2, test=created_test)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2, test=created_test)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2, test=created_test)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()
        
        a5.status = Answer.CORRECT
        a5.grade = 1.0
        a5.save()
        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()
        
        tu1 = TestUserRelation.objects.create(student=user1, test=created_test, index_list="[0,1,2,3]")
        tu1.save()
        
        tu2 = TestUserRelation.objects.create(student=user2, test=created_test, index_list="[0,1,2,3]")
        tu2.save()

        self.client.login(username="superbaa", password="foo")
        response = self.client.get(f"/mydidata/test_progress/{created_test.uuid}/{classroom.id}/")

        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Aproveitamento")
        self.assertContains(response, "User1")
        self.assertContains(response, "<td>10")

        self.assertContains(response, "User2")
        self.assertContains(response, "<td>6,875")

    def test_progress_view(self):
        superuser = User.objects.create_superuser(email='normal@superuser1.com', username='superbaa', password='foo')
        superuser.set_password("foo")
        superuser.save()

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo', first_name="User1", last_name="Baa")
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo', first_name="User2", last_name="Baa")
        user2.set_password("foo")
        user2.save()

        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        created_test = Test.objects.create(title="My Test", topic=topic)

        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = created_test.questions.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        q4 = created_test.questions.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)

        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1, test=created_test)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1, test=created_test)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1, test=created_test)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1, test=created_test)

        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2, test=created_test)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2, test=created_test)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2, test=created_test)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2, test=created_test)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()
        
        a5.status = Answer.CORRECT
        a5.grade = 1.0
        a5.save()
        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()
        
        tu1 = TestUserRelation.objects.create(student=user1, test=created_test, index_list="[0,1,2,3]")
        tu1.save()
        
        tu2 = TestUserRelation.objects.create(student=user2, test=created_test, index_list="[0,1,2,3]")
        tu2.save()

        self.client.login(username="superbaa", password="foo")
        response = self.client.get(f"/mydidata/calculate_student_grades/{created_test.id}/{user1.id}/")

        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Aproveitamento")
        self.assertContains(response, "User1")
        self.assertContains(response, "<td>10")

        self.assertNotContains(response, "User2")
        self.assertNotContains(response, "<td>6,875")

        response = self.client.get(f"/mydidata/calculate_student_grades/{created_test.id}/{user2.id}/")

        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Aproveitamento")
        self.assertNotContains(response, "User1")
        self.assertNotContains(response, "<td>10")

        self.assertContains(response, "User2")
        self.assertContains(response, "<td>6,875")

    def test_assess_view_test(self):
        superuser = User.objects.create_superuser(email='normal@superuser1.com', username='superbaa', password='foo')
        superuser.set_password("foo")
        superuser.save()

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo', first_name="User1", last_name="BAA")
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo', first_name="User2", last_name="Baa")
        user2.set_password("foo")
        user2.save()

        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = superuser)
        
        created_test = Test.objects.create(title="My Test", topic=topic)

        q1 = created_test.questions.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        c1q1 = q1.choices.create(choice_text = "choice 1", is_correct=True)
        c2q1 = q1.choices.create(choice_text = "choice 2")
        c3q1 = q1.choices.create(choice_text = "choice 3")
        c4q1 = q1.choices.create(choice_text = "choice 4")
        
        q2 = created_test.questions.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        c1q2 = q2.choices.create(choice_text = "choice 1")
        c2q2 = q2.choices.create(choice_text = "choice 2")
        c3q2 = q2.choices.create(choice_text = "choice 3", is_correct=True)
        c4q2 = q2.choices.create(choice_text = "choice 4")
        

        a1 = Answer.objects.create(choice=c1q2, question=q1, student=user1, test=created_test)
        a2 = Answer.objects.create(choice=c2q2, question=q2, student=user1, test=created_test)
        
        a3 = Answer.objects.create(choice=c1q1, question=q1, student=user2, test=created_test)
        a4 = Answer.objects.create(choice=c3q2, question=q2, student=user2, test=created_test)

        self.client.login(username="superbaa", password="foo")
        response = self.client.get(f"/mydidata/test/assess/{classroom.id}/{created_test.uuid}/")
        self.assertRedirects(
            response, f'/mydidata/test_progress/{created_test.uuid}/{classroom.id}/', 
            status_code=302, target_status_code=200, 
            fetch_redirect_response=True
        )

    
    


class QuestionTests(TestCase):
    def test_question_is_discursive(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_1.topic = topic
        choice_1 = Choice.objects.create(question=question_1, is_correct=False, choice_text="choice 1" )
        
        self.assertFalse(question_1.is_discursive())
    
        
class TopicTest(TestCase):
    def test_get_latest_version(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", topic_content = "hello world", order=1, owner = user)
        version = topic.get_latest_approved_version()
        self.assertEqual(version.content, "hello world")
    
    def test_merge_version(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", topic_content = "hello world", order=1, owner = user)
        first_version = ContentVersion.objects.create(topic=topic, user=user, content="hello world", approved=True)
        second_version = ContentVersion.objects.create(topic=topic, user=user, content="first edition", approved=False)

        topic.update_to_version(second_version.id)

        saved_topic = Topic.objects.get(pk=topic.id)
        self.assertEqual("first edition", saved_topic.topic_content)

        saved_version = ContentVersion.objects.get(pk=second_version.id)
        self.assertEqual(second_version, saved_version)
    
    def test_is_closed_for_student(self):
        owner = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        student = User.objects.create_user(email='student@user.com', username='std', password='foo')
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(student)
        topic = Topic.objects.create(topic_title="Test Topic", topic_content = "hello world", order=1, owner = owner)
        self.assertFalse(topic.is_closed_for(student))
        classroom.closed_topics.add(topic)
        self.assertTrue(topic.is_closed_for(student))

        


class TopicIntegration(TestCase):

    def test_new_version_creation(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        form = TopicForm(data={"topic_content": 'hello world', "topic_title": 'test topic', "order": 1, "owner":user.pk,}, owner=user)
        if not form.is_valid():
            print("form errors", form.errors)

        saved_topic = form.save()
        
        self.assertEqual(saved_topic.topic_content, "hello world")

        self.assertEqual(1, len(saved_topic.versions.all()))
        
        self.assertEqual("hello world", saved_topic.versions.all().first().content)

    def test_calcualte_grades_avg(self):

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)
        
        non_topic_question = Question.objects.create(question_text= "question 2", uuid="5", difficulty_level = 1, question_type=3)
        non_topic_answer = Answer.objects.create(answer_text="answer question 1", question=non_topic_question, student=user1)

        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1)
        
        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        a5.status = Answer.CORRECT
        a5.grade = 1.0
        a5.save()
        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()

        expected_grades = [[user1, 10.0], [user2, 6.875]]

        self.assertEqual(topic.calculate_grades(classroom), expected_grades)

    def test_calcualte_grades_avg_missing_answer(self):

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)
        
        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1)
        
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()

        expected_grades = [[user1, 10.0], [user2, 4.375000000000001]]

        self.assertEqual(topic.calculate_grades(classroom), expected_grades)

    def test_calcualte_grades_avg_user_no_answer(self):

        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()

        no_answer_user = User.objects.create_user(email='normal@no_answer_user.com', username='baa3', password='foo')
        no_answer_user.set_password("foo")
        no_answer_user.save()
        
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)
        classroom.students.add(no_answer_user)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", difficulty_level = 1, question_type=3)
        
        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1)
        
        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        a5.status = Answer.CORRECT
        a5.grade = 1.0
        a5.save()
        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()

        expected_grades = [[user1, 10.0], [user2, 6.875], [no_answer_user, 0.0]]

        self.assertListEqual(topic.calculate_grades(classroom), expected_grades)

    def test_calcualte_grades_with_weights(self):
        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", weight = 0.6, difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", weight = 0.1, difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", weight = 0.1, difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", weight = 0.2, difficulty_level = 1, question_type=3)
        
        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1)
        
        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        a5.status = Answer.CORRECT
        a5.grade = 1.0
        a5.save()
        a6.status = Answer.CORRECT
        a6.grade = 0.8
        a6.save()
        a7.status = Answer.CORRECT
        a7.grade = 0.65
        a7.save()
        a8.status = Answer.CORRECT
        a8.grade = 0.3
        a8.save()

        expected_grades = [[user1, 10.0], [user2, 8.0]]

        self.assertListEqual(topic.calculate_grades_wavg(classroom), expected_grades)

    def test_calcualte_grades_with_team_answers_avg(self):
        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()

        team1 = Team.objects.create(name="Winners", owner=user1)
        team1.members.add(user1)
        team1.members.add(user2)

        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", weight = 0.6, difficulty_level = 1, is_team_work=True, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", weight = 0.1, difficulty_level = 1, is_team_work=True, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", weight = 0.1, difficulty_level = 1, is_team_work=True, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", weight = 0.2, difficulty_level = 1, is_team_work=True, question_type=3)

        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1, team=team1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1, team=team1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1, team=team1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1, team=team1)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        expected_grades = [[user1, 10.0], [user2, 10.0]]
        

        self.assertListEqual(topic.calculate_grades(classroom), expected_grades)

    def test_calcualte_grades_with_team_answers_wavg(self):
        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()
        
        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()
        
        team1 = Team.objects.create(name="Winners", owner=user1)
        team1.members.add(user1)
        team1.members.add(user2)
        
        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", is_team_work=True, weight = 0.6, difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", is_team_work=True, weight = 0.1, difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", is_team_work=True, weight = 0.1, difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", is_team_work=True, weight = 0.2, difficulty_level = 1, question_type=3)
        
        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1, team=team1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1, team=team1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1, team=team1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1, team=team1)

        a1.status = Answer.CORRECT
        a1.grade = 1.0
        a1.save()
        a2.status = Answer.CORRECT
        a2.grade = 1.0
        a2.save()
        a3.status = Answer.CORRECT
        a3.grade = 1.0
        a3.save()
        a4.status = Answer.CORRECT
        a4.grade = 1.0
        a4.save()

        expected_grades = [[user1, 10.0], [user2, 10.0]]

        self.assertEqual(topic.calculate_grades_wavg(classroom), expected_grades)

class ContentVersionTest(TestCase):
    def test_new_version(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", topic_content = "hello world", order=1, owner = user)

        form = ContentVersionForm(data={"content": "First Version"}, user=user, topic=topic)

        self.assertTrue(form.is_valid())

    
    def test_edit_topic_with_form(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", topic_content = "hello world", order=1, owner = user)
        first_version = ContentVersion.objects.create(topic=topic, user=user, content="hello world")
        
        form = ContentVersionForm(instance=first_version, user =user, data={'content': "first edition"})
        
        self.assertTrue(form.is_valid())
        
        form.save()
    
        saved_topic = Topic.objects.get(pk=topic.id)
        self.assertEqual("hello world", saved_topic.topic_content)
    
        approved_version = ContentVersion.objects.filter(topic=saved_topic).first()
        self.assertEqual("first edition", approved_version.content)
    
    
    def test_diff(self):
        topic_text = """
        <h2>Sum&aacute;rio</h2>

          <ol>
          	<li>Introdu&ccedil;&atilde;o</li>
          	<li>Ligando e Desligando o PC com Seguran&ccedil;a</li>
          	<li>&Aacute;rea de Trabalho</li>
          	<li>Acessando os Drives do PC: o&nbsp;explorador de arquivos</li>
          	<li>Entendendo as Janelas do Windows</li>
          </ol>

          <h2>Introdu&ccedil;&atilde;o paoidfjapiodf</h2>

          <p>Neste m&oacute;dulo, voc&ecirc; vai aprender como iniciar e desligar corretamente o seu PC, gerenciar janelas, arquivos e pastas no Windows. Aperte os sintos e boa divers&atilde;o ;-)!<br />
          <br />
          O sistema operacional &eacute; um software que permite o uso do computador e seus dispositivos de Hardware. Atrav&eacute;s dele n&oacute;s podemos instalar aplicativos, acessar arquivos e pastas gravados e controlar dispositivos, como o volume dos auto-falantes e o brilho do monitor, por exemplo. Atualmente h&aacute; diversos Sistemas Operacionais no mercado, tanto para computadores pessoais como para smartphones.</p>

          <p><img src="https://drive.google.com/uc?export=view&amp;id=1s0fFHM9xxYpL6iwCu0R5MokJZ5wDqeQ-" style="height:69px; width:250px" /></p>

          <p>Quando ligamos o computador, o primeiro programa que &eacute; carregado &eacute; o&nbsp;Sistema Operacional. Ap&oacute;s isso, podemos utilizar o computador de fato.</p>

          <h2>Ligando e Desligando o PC com Seguran&ccedil;a</h2>

          <p>Para ligar o computador, precisamos primeiro ligar o estabilizador.</p>

          <p><img src="https://drive.google.com/uc?export=view&amp;id=1VmRz-ZGW_IzhV3yB92PTwy17XKuduQBJ" style="height:143px; width:200px" /></p>

          <p>Este componente, protege o computador de eventuais sobrecargas na rede el&eacute;trica. Quando h&aacute; um aumento de tens&atilde;o na rede el&eacute;trica, o establizador entra em a&ccedil;&atilde;o e faz o nivelamento da tens&atilde;o que passa para o seu computador. Al&eacute;m disso, caso a sobrecarga seja muito forte, o estabilizador acaba queimando o seu fus&iacute;vel antes que o computador seja atingido.</p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px; text-align:center"><strong>&Eacute; bom saber!&nbsp;</strong><br />
          <br />
          <img alt="Fontes de notebook, como esta acima, tornaram os estabilizadores dispensÃ¡veis para os eletrÃ´nicos que as possuem (Foto: ReproduÃ§Ã£o)" src="http://s.glbimg.com/po/tt/f/original/2012/06/18/fontes-de-notebook-como-esta-acima-tornaram-os-estabilizadores-dispensaveis-para-os-eletronicos-que-as-possuem-foto-reproducao.jpg" style="float:right; height:120px; width:120px" /><br />
          <br />
          As fontes dos notebooks j&aacute; possuem a fun&ccedil;&atilde;o estabilizadora de f&aacute;brica, cumprindo muito bem esse papel!<br />
          <br />
          <br />
          &nbsp;</div>

          <p>Ap&oacute;s ligar o establizador, ligue o computador e aguarde at&eacute; que o sistema operacional seja carregado.</p>

          <p>Podemos desligar o computador pelo Menu Iniciar, Desligar. Para isso, clique na janelinha na parte inferior da tela e depois clique no bot&atilde;o de desligar. Veja as imagens abaixo:<br />
          <br />
          <strong>1.</strong>&nbsp;<img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/28/window_key.png" style="height:25px; width:200px" /></p>

          <p>&nbsp;</p>

          <p><strong>2.</strong>&nbsp;<img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/28/desl.png" style="height:312px; width:400px" /><br />
          &nbsp;</p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px"><strong><span style="color:#c0392b">Cuidados Importantes!</span></strong><br />
          <br />
          <strong>Sempre desligue o seu PC pelo sistema para n&atilde;o danific&aacute;-lo e preservar seus arquivos. Como o PC &eacute; muito sens&iacute;vel &agrave; cortes abruptos de energia, deslig&aacute;-lo&nbsp;diretamente da tomada pode causar danos aos seus componentes!</strong></div>

          <h2>Tela Inicial e &Aacute;rea de Trabalho</h2>

          <p>Ao finalizar o carregamento do sistema operacional, voc&ecirc; ver&aacute; uma tela para realizar o <strong>login.</strong>&nbsp;<u>O Login &eacute; o processo de autentica&ccedil;&atilde;o de um usu&aacute;rio no computador</u>. Se configurado adequadamente, voc&ecirc; dever&aacute; possuir uma senha para o seu usu&aacute;rio. Basta digitar a senha e teclar ENTER.</p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px"><strong><span style="color:#c0392b">Cuidados Importantes!</span></strong><br />
          <br />
          <strong>Nem sempre o sistema possui um usu&aacute;rio configurado com uma senha, o que pode tornar o seu computador vulner&aacute;vel aos&nbsp;programas mal-intencionados, os famosos virus de computador. Al&eacute;m disso, voc&ecirc; tamb&eacute;m pode virar&nbsp;alvo f&aacute;cil de ataques de hackers que podem roubar suas informa&ccedil;&otilde;es ou fazer mal uso do seu computador sem que voc&ecirc; saiba! Mantenha sempre o seu usu&aacute;rio configurado com uma senha forte&nbsp;e modifique a sua senha de tempos em tempos para ficar mais protegido.</strong></div>

          <p>Ap&oacute;s fazer o Login, voc&ecirc; ver&aacute; a Area de Trabalho (tamb&eacute;m chamado <strong>Desktop</strong>). Mais a frente, aprenderemos que a &aacute;rea de trabalho &eacute; apenas uma pasta no seu computador que &eacute; apresentada de modo diferenciado pelo Windows. Observe os principais componentes desta tela detacados em vermelho:</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/16/desktop.png" style="height:413px; width:750px" /></p>

          <p>A janelinha no canto inferior esquerdo &eacute; o bot&atilde;o de acesso ao ponto de partida do Windows. Ao clicar nela, voc&ecirc; ver&aacute; uma lista de comandos do sistema, ao lado esquerdo, e uma lista de programas instalados no seu PC ordenados alfabeticamente.</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/16/menu_iniciar.png" style="height:440px; width:700px" /></p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px; text-align:center"><strong>Dominando Atalhos: Tecla <u>Windows</u></strong>&nbsp;&nbsp;&nbsp;<br />
          <br />
          <br />
          Todo teclado vem com uma tecla Windows. Ao pression&aacute;-la voc&ecirc; <u>abrir&aacute; o Menu Iniciar</u> sem precisar usar o<br />
          mouse. Fa&ccedil;a um teste no seu PC!<br />
          <br />
          <br />
          <img alt="Resultado de imagem para tecla windows" src="https://mydidata2.s3.amazonaws.com/uploads/2020/04/22/windowskey.jpeg" style="height:90px; width:150px" /></div>

          <h2>Acessando os Drives do PC</h2>

          <p>Neste momento, vamos aprender como navegar pelas pastas e arquivos armazenados no seu PC. Veremos que o componente que armazena seus arquivos e pastas &eacute; o <strong>Disco R&iacute;gido</strong>.</p>

          <p>Localize o &iacute;cone do Explorador de Arquivos e d&ecirc; um clique para inici&aacute;-lo:</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/17/exp_arq.png" style="height:149px; width:600px" /></p>

          <p>Para visualizar os dispositivos e as principais pastas do computador, utilize o Explorador de Arquivos e acesse&nbsp;<strong>Este Computador</strong>, como nas imagems abaixo. Voc&ecirc; pode clicar na pastinha na barra de ferramentas no Windows para inici&aacute;-lo. Veja abaixo os componentes do seu PC.</p>

          <p>&nbsp;</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/17/est_comp.png" style="height:354px; width:700px" /></p>

          <p>Na imagem acima podemos visualizar os dispositivos conectados ao computador, incluindo <strong>drives de CD/DVD</strong> e <strong>Pen Drives</strong>.&nbsp;O disco C &eacute; o diret&oacute;rio Raiz, representando o HD do computador.</p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px; text-align:center"><strong>Dominando Atalhos: abrindo&nbsp;o explorador de arquivos</strong><br />
          <br />
          <br />
          Use a combina&ccedil;&atilde;o <strong>tecla Windows + E</strong>&nbsp;para iniciar automaticamente o <u>Explorador de Arquivos</u>. Veja abaixo:<br />
          <br />
          <img alt="Resultado de imagem para tecla windows + E" src="data:image/png;base64,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" /></div>

          <h3>&nbsp;</h3>

          <h2>Gerenciamento de Janelas</h2>

          <p>Uma&nbsp;janela &eacute; um recurso que o sistema oferece para interargirmos com os programas instalados. Cada aplicativo no Windows utiliza uma ou v&aacute;rias janelas. Por exemplo, se voc&ecirc; abriu o programa <u>Explorador de Arquivos</u>, voc&ecirc; est&aacute; com uma de suas janelas abertas. Na sua &aacute;rea de trabalho, voc&ecirc; pode ter v&aacute;rias janelas abertas de programas distintos, por isso, &eacute; muito importante sabermos gerenci&aacute;-las. Veja outros exemplos de janelas.</p>

          <p>&nbsp;</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/27/janelas.png" style="height:419px; width:800px" /></p>

          <p>Janelas podem ser movidas de um lugar para outro na sua tela e&nbsp;redimensionadas.&nbsp;Al&eacute;m disso, podem ser minimizadas, maximizadas ou restauradas. Vamos tentar redimensionar a janela do explorador de arquivos.</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/27/redim1.png" style="height:477px; width:700px" /></p>

          <p>Janelas podem ser gerenciadas pelos bot&otilde;es de Minimizar, Maximizar e Restaurar:</p>

          <p><img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/16/janelas1.png" style="height:385px; width:750px" /></p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px"><strong>Aprenda Fazendo!</strong><br />
          <br />
          Execute os passos&nbsp;abaixo no seu PC:<br />
          <br />
          1 - Minimize a janela. Repare que a janela fica dispon&iacute;vel na barra de ferramentas do Sistema;<br />
          2 - Clique na janela minimizada, dispon&iacute;vel na barra de ferramentas, para que ela seja restaurada;<br />
          3 - Clique em maximizar. Repare que a janela preencheu a tela inteira;<br />
          4 - Clique em restaurar para que a janela deixe de ocupar o espa&ccedil;o inteiro da tela;<br />
          5 - Clique em fechar para encerrar a janela e o programa Explorador de Arquivos.</div>

          <h2>&nbsp;</h2>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px"><strong>Dominando Atalhos: fechando janelas com ALT + F4</strong><br />
          <br />
          Para fechar uma janela sem precisar clicar no bot&atilde;o <strong>[X],&nbsp;</strong>voc&ecirc; pode utilizar a combina&ccedil;&atilde;o <strong>ALT + F4&nbsp;</strong>&nbsp;no seu teclado.<br />
          <img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2020/06/23/alt_f4.jpg" style="height:229px; width:400px" /><br />
          <strong>Fonte:&nbsp;</strong><a href="https://www.techtudo.com.br/dicas-e-tutoriais/noticia/2015/09/conheca-as-funcoes-secretas-do-seu-teclado-e-agilize-seus-trabalhos.html">https://www.techtudo.com.br/dicas-e-tutoriais/noticia/2015/09/conheca-as-funcoes-secretas-do-seu-teclado-e-agilize-seus-trabalhos.html</a><br />
          <br />
          <strong>Experimente no seu computador e tente fechar uma janela somente com o teclado.</strong></div>

          <h2>Posicionando Janelas Lado-a-Lado</h2>

          <p>Um recurso muito &uacute;til que o Windows oferece &eacute; a divis&atilde;o da tela ao meio entre duas janelas. Para isso, basta clicar na barra superior, segurar o clique e arrastar para uma das laterais at&eacute; que o cursor do mouse toque na extremidade da tela. Quando isso ocorrer, basta soltar o clique e selecionar a segunda janela que ir&aacute; dividir a tela com a que voc&ecirc; arrastou.Veja a anima&ccedil;&atilde;o abaixo e tente fazer no seu PC.<br />
          <br />
          <img alt="" src="https://mydidata2.s3.amazonaws.com/uploads/2019/12/28/lado_a_lado.gif" style="height:364px; width:750px" /></p>

          <div style="background:#eeeeee; border:1px solid #cccccc; padding:5px 10px; text-align:center"><strong>Dominando Atalhos</strong>&nbsp;&nbsp;&nbsp;<br />
          <br />
          <br />
          Voc&ecirc; pressionar a combina&ccedil;&atilde;o <u>Window + seta para direita ou esquerda</u>&nbsp;para fazer a divis&atilde;o da tela. Veja:<br />
          <img alt="Resultado de imagem para window arrow key" src="https://mydidata2.s3.amazonaws.com/uploads/2020/04/22/arrow_key.jpg" style="height:150px; width:150px" /></div>

          <h2>Precisa de um Refor&ccedil;o?</h2>

          <h4>Veja esta sequ&ecirc;ncia bem bacana de v&iacute;deo-aulas:</h4>

          <h4>V&iacute;deo Aula: Gerenciamento de Janelas</h4>

          <h4><iframe frameborder="0" height="315" src="https://www.youtube.com/embed/sbrNx_m6zBQ" width="560"></iframe></h4>

          """
        
        version_text = topic_text
        version_text += "asdfadsfadsf"

        
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_content = topic_text, topic_title="test", order=1, owner=user)
        version = ContentVersion.objects.create(topic=topic, content=version_text, user=user)

class TasksTest(TestCase):

    def test_detect_copies(self):
        user1 = User.objects.create_user(email='normal@user1.com', username='baa', password='foo')
        user1.set_password("foo")
        user1.save()

        user2 = User.objects.create_user(email='normal@user2.com', username='baa2', password='foo')
        user2.set_password("foo")
        user2.save()

        classroom = Classroom.objects.create(name="Test Class")
        classroom.students.add(user1)
        classroom.students.add(user2)

        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user1)
        q1 = topic.question_set.create(question_text= "question 1", uuid="1", punish_copies=True, difficulty_level = 1, question_type=3)
        q2 = topic.question_set.create(question_text= "question 2", uuid="2", punish_copies=True, difficulty_level = 1, question_type=3)
        q3 = topic.question_set.create(question_text= "question 1", uuid="3", punish_copies=True, difficulty_level = 1, question_type=3)
        q4 = topic.question_set.create(question_text= "question 2", uuid="4", punish_copies=True, difficulty_level = 1, question_type=3)

        a1 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user1)
        a2 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user1)
        a3 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user1)
        a4 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user1)

        a5 = Answer.objects.create(answer_text="answer question 1", question=q1, student=user2)
        a6 = Answer.objects.create(answer_text="answer question 2", question=q2, student=user2)
        a7 = Answer.objects.create(answer_text="answer question 3", question=q3, student=user2)
        a8 = Answer.objects.create(answer_text="answer question 4", question=q4, student=user2)

        copies = detect_copies([a1,a2,a3,a4])
        expected_response = [[a1, a5], [a2,a6], [a3, a7], [a4, a8]]
        self.assertListEqual(copies, expected_response)



        


        
        
            






            
    
# class SimpleTest(TestCase):
    # def setUp(self):
        # Every test needs access to the request factory.
        # self.factory = RequestFactory()
# 
    # def test_details(self):
        # Create an instance of a GET request.
        # request = self.factory.get('/')
        # request.user = AnonymousUser()
# 
        # Test my_view() as if it were deployed at /customer/details
        # response = index(request)
        # self.assertEqual(response.status_code, 200)


