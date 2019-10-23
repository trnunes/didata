from django.contrib import admin

from django import forms
from django.contrib import admin
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Question, Discipline
from .models import Choice, Topic, Test, Answer, MultipleChoiceAnswer, DiscursiveAnswer, Classroom, ResourceRoom
from django.utils.safestring import mark_safe


class MultipleChoiceAnswerInline(admin.TabularInline):
    model = MultipleChoiceAnswer
    extra = 1

class DiscursiveAnswerInline(admin.TabularInline):
    model = DiscursiveAnswer
    extra = 1

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionInline(admin.StackedInline):
    model = Question
    question_text = forms.CharField(widget=CKEditorUploadingWidget())
    readonly_fields = ('question_link',) 
    def question_link(self, obj):
        question_url = "/admin/mydidata/question/"+str(obj.id)+"/change/"
        return mark_safe('<a href="%s">%s</a>' % (question_url, "visualizar"))
    question_link.allow_tags = True
    extra = 1
    
class TopicInline(admin.TabularInline):
    model = Topic
    exclude = ('topic_content',)
    readonly_fields = ('edit_link', )
    def edit_link(self, obj):
        return mark_safe('<a href="%s">%s</a>'%(obj.get_admin_url(), obj.topic_title))
    edit_link.allow_tags = True
    extra = 1
    ordering = ('order',)
            
class QuestionAdminForm(forms.ModelForm):
    question_text = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Question
        fields = '__all__'
        
class ClassroomAdmin(admin.ModelAdmin):
    model = Classroom
    filter_horizontal = ('students', 'disciplines', 'closed_topics',)

class ResourceRoomAdmin(admin.ModelAdmin):
    model = ResourceRoom
    filter_horizontal = ('students', 'topics',)

class DisciplineAdmin(admin.ModelAdmin):
    model = Discipline
    filter_horizontal = ('students',)
    inlines = [
        TopicInline,
    ]
    
    
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    inlines = [
        ChoiceInline,
        MultipleChoiceAnswerInline,
        DiscursiveAnswerInline,
    ]
    
class TopicAdminForm(forms.ModelForm):
    topic_content = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Topic
        fields = '__all__'

class TopicAdmin(admin.ModelAdmin):
    form = TopicAdminForm
    show_change_link = True
    inlines = [
        QuestionInline,
    ]
    
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(MultipleChoiceAnswer)
admin.site.register(DiscursiveAnswer)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Classroom, ClassroomAdmin)
admin.site.register(ResourceRoom, ResourceRoomAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Test)


# Register your models here.

