from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey("account.User",on_delete=models.SET_NULL,null=True,blank=True,related_name="%(class)s_created",)
    updated_by = models.ForeignKey("account.User",on_delete=models.SET_NULL,null=True,blank=True,related_name="%(class)s_updated",)

    class Meta:
        abstract = True
