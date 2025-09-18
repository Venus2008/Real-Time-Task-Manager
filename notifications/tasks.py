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

    subject = f"📌 New Task Assigned: {task.title}"

    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <tr>
                <td style="background-color: #4CAF50; color: white; padding: 16px; border-radius: 8px 8px 0 0; text-align: center; font-size: 20px;">
                    🚀 New Task Assigned
                </td>
            </tr>
            <tr>
                <td style="padding: 20px; color: #333;">
                    <p>Hello <b>{task.assigned_to.name or 'Employee'}</b>,</p>
                    <p>You have been assigned a new task:</p>
                    <table width="100%" cellpadding="8" style="border-collapse: collapse; margin-top: 10px;">
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold; width: 120px;">Title</td>
                            <td>{task.title}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Description</td>
                            <td>{task.description or "No description provided"}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Due Date</td>
                            <td>{task.due_date.strftime('%d %B %Y') if task.due_date else "Not set"}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Priority</td>
                            <td>{task.priority.capitalize() if task.priority else "Normal"}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 20px;">Please review the task and get started as soon as possible.</p>
                    <p style="margin-top: 10px;">Thanks,<br><b>{task.created_by.name}</b></p>
                </td>
            </tr>
            <tr>
                <td style="background: #f9f9f9; text-align: center; padding: 10px; font-size: 12px; color: #777; border-top: 1px solid #eee;">
                    This is an automated message. Please do not reply.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    plain_message = f"You have been assigned a new task: {task.title}\nDescription: {task.description}"

    send_mail(
        subject,
        plain_message,  # fallback for plain-text clients
        settings.DEFAULT_FROM_EMAIL,
        [assignee_email],
        fail_silently=False,
        html_message=html_message
    )

@shared_task
def send_task_updated_email(task_id, assignee_email):
    from task.models import Task
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return  # Task not found, do not send email

    subject = f"🔄 Task Updated: {task.title}"

    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <tr>
                <td style="background-color: #2196F3; color: white; padding: 16px; border-radius: 8px 8px 0 0; text-align: center; font-size: 20px;">
                    🔄 Task Updated
                </td>
            </tr>
            <tr>
                <td style="padding: 20px; color: #333;">
                    <p>Hello <b>{task.assigned_to.name or 'Employee'}</b>,</p>
                    <p>The following task has been <b>updated</b>. Please review the latest details:</p>
                    
                    <table width="100%" cellpadding="8" style="border-collapse: collapse; margin-top: 10px;">
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold; width: 120px;">Title</td>
                            <td>{task.title}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Description</td>
                            <td>{task.description or "No description provided"}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Due Date</td>
                            <td>{task.due_date.strftime('%d %B %Y') if task.due_date else "Not set"}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Priority</td>
                            <td>{task.priority.capitalize() if task.priority else "Normal"}</td>
                        </tr>
                        <tr>
                            <td style="background: #f2f2f2; font-weight: bold;">Status</td>
                            <td>{task.status.replace("_", " ").title()}</td>
                        </tr>
                    </table>

                    <p style="margin-top: 20px;">Make sure to check the changes and proceed accordingly.</p>
                    <p style="margin-top: 10px;">Thanks,<br><b>{task.created_by.name}</b></p>
                </td>
            </tr>
            <tr>
                <td style="background: #f9f9f9; text-align: center; padding: 10px; font-size: 12px; color: #777; border-top: 1px solid #eee;">
                    This is an automated message. Please do not reply.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    plain_message = f"Task '{task.title}' has been updated. Please check the details."

    send_mail(
        subject,
        plain_message,  # fallback for plain-text clients
        settings.DEFAULT_FROM_EMAIL,
        [assignee_email],
        fail_silently=False,
        html_message=html_message
    )

@shared_task
def send_pending_task_reminders():
    users_with_tasks = {}
    pending_tasks = Task.objects.filter(status=StatusChoice.PENDING, is_archived=False)

    for task in pending_tasks:
        if task.assigned_to:
            users_with_tasks.setdefault(task.assigned_to.email, []).append(task.title)

    for email, tasks in users_with_tasks.items():
        subject = "⏳ Reminder: Pending Tasks"

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" 
                   style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; 
                          box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                <tr>
                    <td style="background-color: #ff9800; color: white; padding: 16px; 
                               border-radius: 8px 8px 0 0; text-align: center; font-size: 20px;">
                        ⏳ Pending Task Reminder
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px; color: #333;">
                        <p>Hello,<b>{task.assigned_to.name or 'Employee'}</b>,</p>
                        <p>You still have the following <b>pending tasks</b> to start working on:</p>
                        <ul>
                            {''.join(f'<li>{t}</li>' for t in tasks)}
                        </ul>
                        <p style="margin-top: 20px;">Please prioritize them as soon as possible.</p>
                        <p>Thanks,<br><b>{task.created_by.name}</b></p>
                    </td>
                </tr>
                <tr>
                    <td style="background: #f9f9f9; text-align: center; padding: 10px; 
                               font-size: 12px; color: #777; border-top: 1px solid #eee;">
                        This is an automated reminder. Please do not reply.
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        plain_message = "You still have these pending tasks:\n" + "\n".join(tasks)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )


@shared_task
def send_inprogress_task_reminders():
    users_with_tasks = {}
    in_progress_tasks = Task.objects.filter(status=StatusChoice.IN_PROGRESS, is_archived=False)

    for task in in_progress_tasks:
        if task.assigned_to:
            users_with_tasks.setdefault(task.assigned_to.email, []).append(task.title)

    for email, tasks in users_with_tasks.items():
        subject = "📝 Reminder: Share Updates for In-Progress Tasks"

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" 
                   style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; 
                          box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                <tr>
                    <td style="background-color: #2196F3; color: white; padding: 16px; 
                               border-radius: 8px 8px 0 0; text-align: center; font-size: 20px;">
                        📝 In-Progress Task Reminder
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px; color: #333;">
                        <p>Hello,<b>{task.assigned_to.name or 'Employee'}</b>,</p>
                        <p>You are currently working on the following tasks:</p>
                        <ul>
                            {''.join(f'<li>{t}</li>' for t in tasks)}
                        </ul>
                        <p style="margin-top: 20px;">
                            Please make sure to <b>share your progress updates</b> by the end of the day.
                        </p>
                        <p>Thanks,<br><b>{task.created_by.name}</b></p>
                    </td>
                </tr>
                <tr>
                    <td style="background: #f9f9f9; text-align: center; padding: 10px; 
                               font-size: 12px; color: #777; border-top: 1px solid #eee;">
                        This is an automated reminder. Please do not reply.
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        plain_message = "You are working on these tasks. Please share your progress updates:\n" + "\n".join(tasks)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )



@shared_task
def send_due_date_reminders():
    now = timezone.now()
    today = now.date()

    tasks = Task.objects.filter(
        due_date__lte=today + timedelta(days=5),  # look ahead 5 days
        status__in=[StatusChoice.IN_PROGRESS, StatusChoice.PENDING],
        is_archived=False
    )

    for task in tasks:
        if not task.assigned_to:
            continue

        due_date = task.due_date
        assignee_email = task.assigned_to.email
        subject = f"📅 Reminder: Task '{task.title}' Due Soon"

        # --- 5 days before due date (twice daily) ---
        if today >= due_date - timedelta(days=5) and today < due_date:
            if now.hour in [10, 16]:  # 10 AM & 4 PM
                plain_message = f"Task '{task.title}' is due on {due_date}. Please start preparing!"
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
                    <table width="100%" style="max-width:600px; margin:auto; background:#fff; border-radius:8px;
                           box-shadow:0 2px 6px rgba(0,0,0,0.1);" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="background:#673AB7; color:white; padding:16px; border-radius:8px 8px 0 0; text-align:center; font-size:20px;">
                                📅 Upcoming Task Due
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:20px; color:#333;">
                                <p>Hello,</p>
                                <p>Your task <b>{task.title}</b> is due on <b>{due_date}</b>.</p>
                                <p>Please ensure you’re making progress before the deadline.</p>
                                <p>Thanks,<br><b>Task Manager System</b></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f9f9f9; text-align:center; padding:10px; font-size:12px; color:#777; border-top:1px solid #eee;">
                                This is an automated reminder. Please do not reply.
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [assignee_email],
                    fail_silently=False,
                    html_message=html_message
                )

        # --- On due date ---
        if today == due_date:
            due_time = timezone.datetime.strptime("18:00", "%H:%M").time()
            due_datetime = timezone.make_aware(timezone.datetime.combine(due_date, due_time))
            diff_minutes = int((due_datetime - now).total_seconds() / 60)

            if diff_minutes in {120, 60, 30, 15}:  # 2h, 1h, 30m, 15m left
                plain_message = f"Task '{task.title}' is due today! Deadline in {diff_minutes} minutes."
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
                    <table width="100%" style="max-width:600px; margin:auto; background:#fff; border-radius:8px;
                           box-shadow:0 2px 6px rgba(0,0,0,0.1);" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="background:#E91E63; color:white; padding:16px; border-radius:8px 8px 0 0; text-align:center; font-size:20px;">
                                ⏰ Task Deadline Approaching
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:20px; color:#333;">
                                <p>Hello,</p>
                                <p>Your task <b>{task.title}</b> is due <b>today</b>!</p>
                                <p><b>Deadline:</b> {due_datetime.strftime("%Y-%m-%d %I:%M %p")}</p>
                                <p>You have <b>{diff_minutes} minutes</b> left before the deadline.</p>
                                <p>Please wrap up your work and submit updates on time.</p>
                                <p>Thanks,<br><b>Task Manager System</b></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f9f9f9; text-align:center; padding:10px; font-size:12px; color:#777; border-top:1px solid #eee;">
                                This is an automated reminder. Please do not reply.
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [assignee_email],
                    fail_silently=False,
                    html_message=html_message
                )

