from venv import create
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from mydidata.models import Answer, Test, Topic, TestUserRelation, Question, Choice



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
        
        self.assertEqual(created_test.next_try(user), 2)
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

        self.assertEqual(created_test.next_try(user), 2)
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
    


class QuestionTests(TestCase):
    def test_question_is_discursive(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        question_1 = Question.objects.create(question_text= "question 1", uuid="2", difficulty_level = 1, question_type=3)
        question_1.topic = topic
        choice_1 = Choice.objects.create(question=question_1, is_correct=False, choice_text="choice 1" )
        
        self.assertFalse(question_1.is_discursive())
    
        

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


