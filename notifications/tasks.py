from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from task.models import Task

@shared_task
def send_task_assigned_email(task_id, assignee_email):
    from task.models import Task
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return  # Task not found, do not send email

    subject = f"New Task Assigned: {task.title}"
    message = f"You have been assigned a new task: {task.title}\nDescription: {task.description}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [assignee_email],fail_silently=False)

@shared_task
def send_task_updated_email(task_id, assignee_email):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return  # Task not found, do not send email
    subject = f"Task Updated: {task.title}"
    message = f"Task '{task.title}' has been updated. Please check the details."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [assignee_email],fail_silently=False)

@shared_task
def send_daily_pending_reminders():
    users_with_tasks = {}
    pending_tasks = Task.objects.filter(status="PENDING",is_archived=False)
    for task in pending_tasks:
        if task.assigned_to:
            users_with_tasks.setdefault(task.assigned_to.email, []).append(task.title)

    for email, tasks in users_with_tasks.items():
        subject = "Daily Pending Task Reminder"
        message = "You still have these pending tasks:\n" + "\n".join(tasks)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
