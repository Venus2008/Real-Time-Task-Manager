from django.db import models
from django.conf import settings
from task.enums import StatusChoice,PriorityChoice
from Backend.models import BaseModel


class Task(BaseModel,models.Model):
    title       = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    file        = models.FileField(
        upload_to='task_files/',
        null=True,
        blank=True
    )
    priority    = models.CharField(
        choices=PriorityChoice.choices,
        max_length=10,
        default='MEDIUM'
    )
    status      = models.CharField(
        choices=StatusChoice.choices,max_length=15,
        default='PENDING'
        )
    is_archived = models.BooleanField(default=False)
    assigned_to =models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_assigned'
        )
    due_date    = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.status} - {self.priority})"
    
    
