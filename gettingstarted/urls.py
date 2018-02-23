from django.conf.urls import include, url
from django.urls import path

from django.contrib import admin
from django.contrib.auth import views as auth_views
admin.autodiscover()

import mydidata.views
from django.conf import settings
from django.views.static import serve
# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', mydidata.views.index, name='index'),
    url(r'^accounts/', auth_views.login, {'template_name': 'mydidata/login.html'}),
    # url(r'^db', mydidata.views.db, name='db'),
    url(r'^mydidata/', include('mydidata.urls')),
    path('admin/', admin.site.urls),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
