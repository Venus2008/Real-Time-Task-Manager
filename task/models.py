from django.db import models
from django.conf import settings

STATUS_CHOICES=(
    ('PENDING','PENDING'),
    ('IN_PROGRESS','IN_PROGRESS'),
    ('COMPLETED','COMPLETED'),
    ("ARCHIVED", "ARCHIVED"),
)

PRIORITY_CHOICES=(
    ('LOW','LOW'),
    ('MEDIUM','MEDIUM'),
    ('HIGH','HIGH'),
    ('CRITICAL','CRITICAL'),
)

class Task(models.Model):
    title=models.CharField(max_length=250)
    description=models.TextField(blank=True)
    file=models.FileField(upload_to='task_files/',null=True,blank=True)
    priority=models.CharField(choices=PRIORITY_CHOICES,max_length=10,default='MEDIUM')
    status=models.CharField(choices=STATUS_CHOICES,max_length=15,default='PENDING')

    is_archived = models.BooleanField(default=False)

    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='task_created')
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='task_assigned')

    def __str__(self):
        return f"{self.title} ({self.status} - {self.priority})"
    
    
class TaskUpdate(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="updates")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_updates")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,null=True,blank=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for {self.task.title} by {self.updated_by.email}"