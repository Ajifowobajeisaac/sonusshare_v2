from celery import Celery; app = Celery('sonusshare_v2'); app.config_from_object('django.conf:settings', namespace='CELERY')
