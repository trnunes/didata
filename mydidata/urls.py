from django.conf.urls import url, include
from django.urls import path

from mydidata import views
from django.contrib.auth import views as auth_views
from mydidata.views import HomePage, TopicList, DisciplineList, ClassList, ResourceRoomList, Deadline

app_name = 'mydidata'
urlpatterns = [
     # Marketing pages
    url(r'^$', HomePage.as_view(), name="home"),
    url(r'^content/(?P<label>[\w-]+)$', views.content, name='content'),
    url(r'^signup/(?P<classroom_id>[0-9]+)$', views.subscriber_new, name='sub_new'),
    url(r'^update_profile/(?P<user_id>[0-9]+)$', views.update_profile, name='update_profile'),
    url(r'^search$', views.search, name='search'),
    url(r'^topic_next/(?P<current_id>[0-9]+)$', views.topic_next, name='topic_next'),
    url(r'^topic_edit/(?P<topic_uuid>[\w-]+)/$', views.topic_edit, name='topic_edit'),
    url(r'^topics_by_subject$', views.topics_by_subject, name='topics_by_subject'),
    url(r'^login/$', auth_views.login, {'template_name': 'mydidata/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/mydidata/login/'}, name='logout'),
    url(r'^topics$', TopicList.as_view(), name="topics"),
    url(r'^classes$', ClassList.as_view(), name="classes"),
    url(r'^resource_rooms$', ResourceRoomList.as_view(), name="resource_rooms"),
    url(r'^disciplines/$', DisciplineList.as_view(), name="disciplines"),
    url(r'^topic/(?P<discipline_uuid>[\w-]+)/$', views.topic, name='topic'),
    url(r'^topic_detail/(?P<uuid>[\w-]+)/$', views.topic_detail, name='topic_detail'),
    url(r'^topic_progress/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.topic_progress, name='topic_progress'),

    url(r'^version_detail/(?P<version_id>[0-9]+)/$', views.version_detail, name='version_detail'),
    url(r'^version_compare/(?P<version_id>[0-9]+)/$', views.version_compare, name='version_compare'),
    url(r'^version_update/(?P<version_id>[0-9]+)/$', views.version_update, name='version_update'),
    url(r'^version_edit/(?P<version_id>[0-9]+)/$', views.version_edit, name='version_edit'),
    url(r'^version/(?P<topic_id>[0-9]+)/$', views.version, name='version'),
    url(r'^version_list/(?P<topic_id>[0-9]+)/$', views.version_list, name='version_list'),

    url(r'^discipline_detail/(?P<uuid>[\w-]+)/$', views.discipline_detail, name='discipline_detail'),
    url(r'^resource_room_topics/(?P<uuid>[\w-]+)/(?P<resource_room_only>[\w-]+)$', views.resource_room_topics, name='resource_room_topics'),    
    url(r'^topic/close/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_close, name='topic_close'),
    url(r'^topic/open/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_open, name='topic_open'),
    url(r'^topic/assess/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.topic_assess, name='topic_assess'),
    url(r'^topic/grades/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$',views.calculate_grades, name='calculate_grades'),
    url(r'^topic/grades/(?P<class_id>[0-9]+)/$',views.calculate_grades, name='calculate_grades'),
    url(r'^academico/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.academico, name="academico"),
    url(r'^download_grades_by_topic/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.download_grades_by_topic, name="download_grades_by_topic"),
    
    
    url(r'^correct_the_whole_topic/(?P<class_id>[0-9]+)/(?P<topic_uuid>[\w-]+)/$', views.correct_the_whole_topic, name="correct_the_whole_topic"),
    url(r'^test_to_academico/(?P<class_id>[0-9]+)/(?P<test_uuid>[\w-]+)/$', views.test_to_academico, name="test_to_academico"),
    url(r'^send_mail/(?P<class_id>[0-9]+)/$', views.send_mail_to_class, name="send_mail_to_class"),
    url(r'^assessments/$',views.assessments, name='assessments'),
    url(r'^assess_answers/$',views.assess_answers, name='assess_answers'),
    url(r'^tests/(?P<id>[0-9]+)/$', views.test_list, name="tests"),
    url(r'^test_detail/(?P<uuid>[\w-]+)/$', views.test_detail, name='test_detail'),
    url(r'^start_test/(?P<uuid>[\w-]+)/$', views.start_test, name="start_test"),
    url(r'^test/progress/(?P<uuid>[\w-]+)/$',views.test_progress, name='test_progress'),
    url(r'^test/close/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_close, name='test_close'),
    url(r'^test/open/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_open, name='test_open'),
    url(r'^test/assess/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/$',views.test_assess, name='test_assess'),
    url(r'^test_progress/(?P<uuid>[\w-]+)/$', views.test_progress, name='test_progress'),
    url(r'^test_progress/(?P<uuid>[\w-]+)/(?P<class_id>[0-9]+)/$',views.test_progress, name='test_progress'),
    url(r'^delete_test_answer/(?P<id>[0-9]+)/$',views.delete_test_answer, name='delete_test_answer'),
    url(r'^delete_answer/(?P<id>[0-9]+)/$',views.delete_answer, name='delete_answer'),
    url(r'^student_progress/(?P<test_id>[0-9]+)/(?P<student_id>[0-9]+)/$',views.student_progress, name='student_progress'),
    url(r'^profile_detail/(?P<student_id>[0-9]+)/$',views.profile_detail, name='profile_detail'),
    url(r'^close_test_for_student/(?P<test_id>[0-9]+)/(?P<student_id>[0-9]+)/$',views.close_test_for_student, name='close_test_for_student'),
    url(r'^calculate_student_grades/(?P<test_id>[0-9]+)/(?P<student_id>[0-9]+)/$',views.calculate_student_grades, name='calculate_student_grades'),
    url(r'^next_try/(?P<test_user_id>[0-9]+)/$', views.next_try, name='next_try'),
    url(r'^finish_test/(?P<class_id>[0-9]+)/(?P<uuid>[\w-]+)/(?P<key>[\w-]+)/$',views.finish_test, name='finish_test'),
    url(r'^get_corrections/(?P<answer_id>[0-9]+)/$',views.get_corrections, name='get_corrections'),
    url(r'^correct_topic/(?P<topic_uuid>[\w-]+)/(?P<class_id>[0-9]+)/$',views.correct_topic, name='correct_topic'),

    url(r'^question_detail/(?P<uuid>[\w-]+)/$', views.question_detail, name="question_detail"),
    url(r'^multiple_choice_question/(?P<topic_uuid>[\w-]+)/$',views.multiple_choice_question, name='multiple_choice_question'),
    url(r'^discursive_question/(?P<topic_uuid>[\w-]+)/$',views.discursive_question, name='discursive_question'),
    url(r'^c_programming_question/(?P<topic_uuid>[\w-]+)/$',views.c_programming_question, name='c_programming_choice_question'),
    url(r'^multiple_choice_question_edit/(?P<uuid>[\w-]+)/$',views.multiple_choice_question_edit, name='multiple_choice_question_edit'),
    url(r'^discursive_question_edit/(?P<uuid>[\w-]+)/$',views.discursive_question_edit, name='discursive_question_edit'),
    url(r'^c_programming_question_edit/(?P<uuid>[\w-]+)/$',views.c_programming_question_edit, name='c_programming_question_edit'),
    url(r'^question_types/(?P<topic_uuid>[\w-]+)/$',views.question_types, name='question_types'),
    url(r'^multiple_choice_answer/(?P<question_uuid>[\w-]+)/$',views.multiple_choice_answer, name='multiple_choice_answer'),
    url(r'^multiple_choice_answer_detail/(?P<answer_id>[0-9]+)$',views.multiple_choice_answer_detail, name='multiple_choice_answer_detail'),    
    url(r'^discursive_answer/(?P<question_uuid>[\w-]+)/$',views.discursive_answer, name='discursive_answer'),
    url(r'^discursive_answer_test/(?P<question_uuid>[\w-]+)/(?P<test_id>[0-9]+)/$',views.discursive_answer, name='discursive_answer'),
    url(r'^download_answers/(?P<topic_uuid>[\w-]+)/(?P<class_id>[0-9]+)/$',views.download_answers, name='download_answers'),
    
    url(r'^test_answer/(?P<question_uuid>[\w-]+)/(?P<test_id>[0-9]+)/$',views.test_answer, name='test_answer'),
    
    url(r'^discursive_answer_detail/(?P<answer_id>[0-9]+)$',views.discursive_answer_detail, name='discursive_answer_detail'),
    url(r'^detect_answer_text/(?P<answer_id>[0-9]+)$',views.detect_answer_text, name='detect_answer_text'),
    url(r'^feedback/(?P<answer_id>[0-9]+)$',views.feedback, name='feedback'),
    url(r'^graphic_feedback/(?P<answer_id>[0-9]+)$',views.graphic_feedback, name='graphic_feedback'),
    url(r'^test/new/(?P<topic_id>[\w-]+)/$',views.test_new, name='test_new'),
    url(r'^progress/(?P<discipline_name>[\w|\W]+)/$',views.progress, name='progress'),
    

    url(r'^percentage_progress/(?P<class_id>[\w-]+)/$',views.percentage_progress, name='percentage_progress'),
    url(r'^my_progress/(?P<discipline_uuid>[\w-]+)/$',views.my_progress, name='my_progress'),

    url(r'^class_progress/(?P<class_id>[\w-]+)/$',views.class_progress, name='class_progress'),
    url(r'^class_detail/(?P<class_id>[\w-]+)/$',views.class_detail, name='class_detail'),
    
    url(r'^resource_room_progress/(?P<uuid>[\w-]+)/$',views.resource_room_progress, name='resource_room_progress'),    
    url(r'^define_team/$',views.define_team, name='define_team'),
    url(r'^test_job/(?P<answer_id>[0-9]+)$',views.test_job, name='test_job'),
    url(r'^teams/create/$',views.create_team, name='create_team'),
    url(r'^teams/list/$',views.team_list, name='list_teams'),
    url(r'^teams/edit/(?P<id>[0-9]+)/$',views.team_edit, name='edit_team'),
    url(r'^teams/(?P<id>[0-9]+)/$',views.team_detail, name='team_detail'),
    
    url(r'^comment/create/(?P<topic_id>[0-9]+)/$',views.comment_create, name='comment_create'),
    url(r'^comment/update/(?P<id>[0-9]+)/$',views.comment_update, name='comment_update'),
    url(r'^comment/delete/(?P<id>[0-9]+)/$',views.comment_delete, name='comment_delete'),
    url(r'^comment/detail/(?P<id>[0-9]+)/$',views.comment_detail, name='comment_detail'),
    url(r'^comment/create-form/(?P<topic_id>[0-9]+)/$',views.create_comment_form, name='comment_create_form'),

    url(r'^forum/post/list/(?P<topic_id>[0-9]+)/$',views.post_list, name='post_list'),
    url(r'^forum/post/create/(?P<topic_id>[0-9]+)/$',views.post_create, name='post_create'),
    url(r'^forum/post/update/(?P<id>[0-9]+)/$',views.post_update, name='post_update'),
    url(r'^forum/post/delete/(?P<id>[0-9]+)/$',views.post_delete, name='post_delete'),
    url(r'^forum/post/detail/(?P<id>[0-9]+)/$',views.post_detail, name='post_detail'),

    url(r'^forum/reply/create/(?P<post_id>[0-9]+)/$',views.reply_create, name='reply_create'),
    url(r'^forum/reply/update/(?P<id>[0-9]+)/$',views.reply_update, name='reply_update'),
    url(r'^forum/reply/delete/(?P<id>[0-9]+)/$',views.reply_delete, name='reply_delete'),
    url(r'^forum/reply/detail/(?P<id>[0-9]+)/$',views.reply_detail, name='reply_detail'),
    url(r'^forum/reply/create-form/(?P<post_id>[0-9]+)/$',views.reply_create_form, name='reply_create_form'),

    url(r'^classroom/create/', views.classroom_create, name='classroom_create'),
    
    url(r'^classroom/(?P<uuid>[\w-]+)/update/', views.classroom_update, name='classroom_update'),
    url(r'^classroom/(?P<uuid>[\w-]+)/delete/', views.classroom_delete, name='classroom_delete'),
    
    url(r'^get_classroom_diagnostics/(?P<class_id>[\w-]+)/$', views.get_classroom_diagnostics, name='get_classroom_diagnostics'),

    url(r'^record_duration/(?P<topic_id>[0-9]+)/$',views.record_duration, name='record_duration'),

    url(r'^create-deadline/(?P<topic_id>[0-9]+)/$', views.create_deadline, name='create_deadline'),
    url(r'^edit-deadline/(?P<pk>\d+)/$', views.edit_deadline, name='edit_deadline'),
    url(r'^delete-deadline/(?P<deadline_id>\d+)/$', views.delete_deadline, name='delete_deadline'),

]