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
        t_diff = timedelta(hours=24)
        is_dst = localtime.tzinfo._dst.seconds != 0
        #veririfica se estã em horário de verão e desconta mais uma hora
        if is_dst:
            localtime -= timedelta(hours=1)
            t_diff = timedelta(hours=24)
        print("LOCALTIME: ", localtime)
        for d in deadlines:
            local_due_date = timezone.localtime(d.due_datetime)
            print("Time Diff", local_due_date - localtime)
            print("DUE TIME: ", local_due_date)
            print((d.due_datetime - localtime)  < t_diff)
            if (d.due_datetime - localtime)  <= t_diff and (d.due_datetime >= localtime):
                topic = d.topic 
                classroom = d.classroom
                message_subject = "AprendaFazendo: prazo para atividades em %s encerram hoje!"%topic.topic_title
                message_body = "Acesse suas atividades em: https://aprendafazendo.net/mydidata/topic_detail/%s"%topic.uuid
                for student in classroom.students.all():
                    try:
                        result = send_mail(message_subject, message_body, None, [student.email])
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