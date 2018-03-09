from django.conf.urls import url, include
from mydidata import views
from django.contrib.auth import views as auth_views
from mydidata.views import HomePage, TopicList, DisciplineList

app_name = 'mydidata'
urlpatterns = [
     # Marketing pages
    url(r'^$', HomePage.as_view(), name="home"),
    url(r'^signup/(?P<classroom_id>[0-9]+)$', views.subscriber_new, name='sub_new'),
    url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    url(r'^login/$', auth_views.login, {'template_name': 'mydidata/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/mydidata/login/'}, name='logout'),
    url(r'^topics$', TopicList.as_view(), name="topics"),
    url(r'^disciplines/$', DisciplineList.as_view(), name="disciplines"),
    url(r'^topic_detail/(?P<uuid>[\w-]+)/$', views.topic_detail, name='topic_detail'),
    url(r'^discipline_detail/(?P<uuid>[\w-]+)/$', views.discipline_detail, name='discipline_detail'),
    url(r'^topic/new/$',views.topic_cru, name='topic_new'),
    url(r'^edit/(?P<uuid>[\w-]+)/$', views.topic_cru, name='topic_update'),
    url(r'^question_detail/$', views.question_detail, name="question_detail"),
    url(r'^question/new/$',views.question_cru, name='question_new'),
    url(r'^question_edit/(?P<uuid>[\w-]+)/$',views.question_cru, name='question_update'),
    url(r'^multiple_choice_answer/(?P<question_uuid>[\w-]+)/$',views.multiple_choice_answer, name='multiple_choice_answer'),
    url(r'^multiple_choice_answer_detail/(?P<answer_id>[0-9]+)$',views.multiple_choice_answer_detail, name='multiple_choice_answer_detail'),
    url(r'^discursive_answer/(?P<question_uuid>[\w-]+)/$',views.discursive_answer, name='discursive_answer'),
    url(r'^discursive_answer_detail/(?P<answer_id>[0-9]+)$',views.discursive_answer_detail, name='discursive_answer_detail'),
    url(r'^test/new/(?P<topic_id>[\w-]+)/$',views.test_new, name='test_new'),
    url(r'^progress/(?P<discipline_name>[\w|\W]+)/$',views.progress, name='progress'),
    url(r'^my_progress/$',views.my_progress, name='my_progress'),
    url(r'^class_progress/(?P<class_id>[\w-]+)/$',views.class_progress, name='class_progress'),
    url(r'^define_team/$',views.define_team, name='define_team'),
    
]