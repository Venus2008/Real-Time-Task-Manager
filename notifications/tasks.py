from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from task.models import Task
from task.enums import StatusChoice

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
def send_pending_task_reminders():
    users_with_tasks = {}
    pending_tasks = Task.objects.filter(status=StatusChoice.PENDING,is_archived=False)
    for task in pending_tasks:
        if task.assigned_to:
            users_with_tasks.setdefault(task.assigned_to.email, []).append(task.title)

    for email, tasks in users_with_tasks.items():
        subject = "Reminder: Pending Tasks"
        message = "You still have these pending tasks:\n" + "\n".join(tasks)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email],fail_silently=False)


@shared_task
def send_inprogress_task_reminders():
    users_with_tasks = {}
    in_progress_tasks = Task.objects.filter(status=StatusChoice.IN_PROGRESS,is_archived=False)
    for task in in_progress_tasks:
        if task.assigned_to:
            users_with_tasks.setdefault(task.assigned_to.email, []).append(task.title)

    for email, tasks in users_with_tasks.items():
        subject = "Reminder: Share Updates for In-Progress Tasks"
        message =  "You are working on these tasks. Please share your progress updates:\n"+ "\n".join(tasks)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email],fail_silently=False)
