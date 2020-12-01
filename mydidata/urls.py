from django.conf.urls import url, include
from mydidata import views
from django.contrib.auth import views as auth_views
from mydidata.views import HomePage, TopicList, DisciplineList, ClassList, ResourceRoomList, TestList

app_name = 'mydidata'
urlpatterns = [
     # Marketing pages
    url(r'^$', HomePage.as_view(), name="home"),
    url(r'^signup/(?P<classroom_id>[0-9]+)$', views.subscriber_new, name='sub_new'),
    url(r'^update_profile/(?P<user_id>[0-9]+)$', views.update_profile, name='update_profile'),
    url(r'^search$', views.search, name='search'),
    url(r'^topic_next/(?P<current_id>[0-9]+)$', views.topic_next, name='topic_next'),    
    url(r'^login/$', auth_views.login, {'template_name': 'mydidata/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/mydidata/login/'}, name='logout'),
    url(r'^topics$', TopicList.as_view(), name="topics"),
    url(r'^classes$', ClassList.as_view(), name="classes"),
    url(r'^resource_rooms$', ResourceRoomList.as_view(), name="resource_rooms"),
    url(r'^disciplines/$', DisciplineList.as_view(), name="disciplines"),
    url(r'^topic_detail/(?P<uuid>[\w-]+)/$', views.topic_detail, name='topic_detail'),
    url(r'^topic_progress/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.topic_progress, name='topic_progress'),
    url(r'^discipline_detail/(?P<uuid>[\w-]+)/$', views.discipline_detail, name='discipline_detail'),
    url(r'^resource_room_topics/(?P<uuid>[\w-]+)/(?P<resource_room_only>[\w-]+)$', views.resource_room_topics, name='resource_room_topics'),    
    url(r'^topic/close/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_close, name='topic_close'),
    url(r'^topic/open/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_open, name='topic_open'),
    url(r'^topic/assess/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_assess, name='topic_assess'),
    url(r'^topic/grades/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.calculate_grades, name='calculate_grades'),
    url(r'^topic/grades/(?P<class_id>[0-9]+)/$',views.calculate_grades, name='calculate_grades'),
    url(r'^academico/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.academico, name="academico"),
    url(r'^test_to_academico/(?P<class_id>[0-9]+)/(?P<test_uuid>[\w-]+)/$', views.test_to_academico, name="test_to_academico"),
    url(r'^send_mail/(?P<class_id>[0-9]+)/$', views.send_mail_to_class, name="send_mail_to_class"),

    url(r'^tests$', TestList.as_view(), name="tests"),
    url(r'^test_detail/(?P<uuid>[\w-]+)/$', views.test_detail, name='test_detail'),
    url(r'^start_test/(?P<uuid>[\w-]+)/$', views.start_test, name="start_test"),
    url(r'^test/progress/(?P<uuid>[\w-]+)/$',views.test_progress, name='test_progress'),
    url(r'^test/close/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_close, name='test_close'),
    url(r'^test/open/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_open, name='test_open'),
    url(r'^test/assess/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_assess, name='test_assess'),
    url(r'^test/results_sum/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_results_sum, name='test_results_sum'),
    url(r'^test/results_wavg/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_results_wavg, name='test_results_wavg'),
    url(r'^test_progress/(?P<uuid>[\w-]+)/$', views.test_progress, name='test_progress'),
    url(r'^test_progress/(?P<uuid>[\w-]+)/(?P<class_id>[0-9]+)/$',views.test_progress, name='test_progress'),
    url(r'^next_try/(?P<test_user_id>[0-9]+)/$', views.next_try, name='next_try'),
    url(r'^detect_copies/(?P<question_uuid>[\w-]+)/$',views.detect_copies, name='detect_copies'),
    url(r'^finish_test/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/(?P<key>[\w-]+)/$',views.finish_test, name='finish_test'),

    url(r'^question_detail/$', views.question_detail, name="question_detail"),
    url(r'^multiple_choice_answer/(?P<question_uuid>[\w-]+)/$',views.answer, name='multiple_choice_answer'),
    url(r'^multiple_choice_answer/(?P<question_uuid>[\w-]+)/(?P<test_id>[0-9]+)/$',views.answer, name='multiple_choice_answer'),
    url(r'^multiple_choice_answer_detail/(?P<answer_id>[0-9]+)$',views.multiple_choice_answer_detail, name='multiple_choice_answer_detail'),    
    url(r'^discursive_answer/(?P<question_uuid>[\w-]+)/$',views.answer, name='discursive_answer'),
    url(r'^discursive_answer_test/(?P<question_uuid>[\w-]+)/(?P<test_id>[0-9]+)/$',views.discursive_answer, name='discursive_answer'),
    url(r'^download_answers/(?P<topic_uuid>[\w-]+)/(?P<class_id>[0-9]+)/$',views.download_answers, name='download_answers'),

    url(r'^discursive_answer_detail/(?P<answer_id>[0-9]+)$',views.discursive_answer_detail, name='discursive_answer_detail'),
    url(r'^feedback/(?P<answer_id>[0-9]+)$',views.feedback, name='feedback'),
    url(r'^test/new/(?P<topic_id>[\w-]+)/$',views.test_new, name='test_new'),
    url(r'^progress/(?P<discipline_name>[\w|\W]+)/$',views.progress, name='progress'),
    

    url(r'^percentage_progress/(?P<class_id>[\w-]+)/$',views.percentage_progress, name='percentage_progress'),
    url(r'^my_progress/$',views.my_progress, name='my_progress'),
    url(r'^class_progress/(?P<class_id>[\w-]+)/$',views.class_progress, name='class_progress'),
    url(r'^resource_room_progress/(?P<uuid>[\w-]+)/$',views.resource_room_progress, name='resource_room_progress'),    
    url(r'^define_team/$',views.define_team, name='define_team'),
    
]