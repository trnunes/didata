from django.core.management.base import BaseCommand, CommandError
from mydidata.models import Deadline
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        notification_errors = []
        deadlines = Deadline.objects.all()
        localtime = timezone.localtime()
        t_diff = timedelta(hours=48)
        is_dst = localtime.tzinfo._dst.seconds != 0
        #veririfica se estã em horário de verão e desconta mais uma hora
        delta_24 = timedelta(hours=24) 
        if is_dst:
            localtime -= timedelta(hours=1)

        
        classrooms_dict = {}
        for d in deadlines:
            local_due_date = timezone.localtime(d.due_datetime)
            if (d.due_datetime - localtime)  <= t_diff and (d.due_datetime >= localtime):
                if d.due_datetime -localtime >= delta_24:
                    due = "amanhã às 23:59:59"
                else:
                    due = "hoje às 23:59:59"
                
                topic = d.topic
                classroom = d.classroom
                if not classrooms_dict.get(classroom, False):
                    classrooms_dict[classroom] = ""
                
                
                message_subject = "AprendaFazendo - Atenção! Prazo para envio de atividades encerrando."
                
                
                classrooms_dict[classroom] += "<li><strong>%s</strong>: %s. Veja <a href='https://aprendafazendo.net/mydidata/topic_detail/%s'><strong>aqui</strong></a> </li> "%(topic.topic_title, due, topic.uuid)
                
        for classroom, message in classrooms_dict.items():
            
           for student in classroom.students.all():
               try:
                   
                   message_body = "<html><body><h2>%s</h2><br/><ul> %s </ul> </body></html>"%(classroom.name, message)
                   result = send_mail(message_subject, message_body, None, [student.email], html_message=message_body)
                   
                   if not result:
                       notification_errors.append((student.email, message_subject, message_body))
               except:
                   notification_errors.append((student.email, message_subject, message_body))
            

        if notification_errors:
            for error in notification_errors:
                error_message_body = "Email: %s\nSubject: %s\nBody: %s"%error
                superuser = User.objects.filter(username="tnunes").first()
                superuser.email_user("AprendaFazendo: Notification errors", error_message_body)
        return