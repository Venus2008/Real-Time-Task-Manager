from django.db import models
from django.utils.translation import gettext_lazy as _

class NotificationType(models.TextChoices):
    TASK_ASSIGNED = "task_assigned", _("Task Assigned")
    TASK_UPDATED = "task_updated", _("Task Updated")
    TASK_COMPLETED = "task_completed", _("Task Completed")
    GENERAL = "general", _("General")
