from django.db import models
from django.conf import settings
from Backend.models import BaseModel
from task.models import Task
from task.enums import StatusChoice
from notifications.enums import NotificationType

class Notification(BaseModel,models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    event = models.CharField(choices=NotificationType.choices,max_length=20,null=True,blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    status = models.CharField(choices=StatusChoice.choices, max_length=20, null=True, blank=True)  
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.event} - {self.task.title if self.task else 'No Task'}"


