from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from task.models import Task
from task.enums import StatusChoice

from django.utils import timezone
from datetime import timedelta



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



@shared_task
def send_due_date_reminders():
    now = timezone.now()
    today = now.date()
    tasks = Task.objects.filter(due_date__lte=today + timezone.timedelta(days=1), status = StatusChoice.IN_PROGRESS, is_archived=False)
    for task in tasks:
        if not task.assigned_to:
            continue

        due_date = task.due_date
        assignee_email = task.assigned_to.email
        subject = f"Reminder: Task '{task.title}' Due Soon"
        
        # --- 5 days before due date ---
        if today >= due_date - timedelta(days=5) and today < due_date:
            if now.hour in [10, 16]:  # twice daily
                message = f"Task '{task.title}' is due on {due_date}. Please start preparing!"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [assignee_email])

        # --- On due date ---
        if today == due_date:
            # Actually calculate exact time difference in minutes
            due_datetime = timezone.make_aware(timezone.datetime.combine(due_date, timezone.datetime.max.time()))
            diff_minutes = int((due_datetime - now).total_seconds() / 60)

            if diff_minutes in {120, 60, 30, 15}:  # 2h, 1h, 30m, 15m
                message = f"Task '{task.title}' is due today! Deadline in {int(diff_minutes)} minutes."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [assignee_email])

