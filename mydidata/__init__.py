
from .celery import app as celery_app

__all__ = ['celery_app']

def autodiscover():
    """
    Autodiscover tasks.py files in much the same way as admin app
    """
    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        try:
            app_path = import_module(app).__path__
        except (AttributeError, ImportError):
            continue
        try:
            imp.find_module('tasks', app_path)
        except ImportError:
            continue

        import_module("%s.tasks" % app)