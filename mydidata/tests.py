from venv import create
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from mydidata.models import Test, Topic, TestUserRelation, Question



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
        question_1 = Question.objects.create(question_text= "question 1", difficulty_level = 1, question_type=3)
        question_2 = Question.objects.create(question_text= "question 2", difficulty_level = 1, question_type=3)
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
    
    def test_is_closed(self):
        user = User.objects.create_user(email='normal@user.com', username='baa', password='foo')
        topic = Topic.objects.create(topic_title="Test Topic", order=1, owner = user)
        created_test = Test.objects.create(title="My Test", topic=topic)
        self.assertFalse(created_test.is_closed_for(user))



        

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


