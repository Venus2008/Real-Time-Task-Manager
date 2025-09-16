import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backend.settings")

app = Celery("Backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send-daily-pending-reminders": {
        "task": "notifications.tasks.send_pending_task_reminders",
        "schedule": crontab(hour=9, minute=0),  # every day at 9:00 AM
    },
    "send-daily-inprogress-reminders": {
        "task": "notifications.tasks.send_inprogress_task_reminders",
        "schedule": crontab(hour=16, minute=0),  # every day at 5:00 PM
    },
}