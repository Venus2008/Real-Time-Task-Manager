from django.db import models
<<<<<<< Updated upstream
from django.conf import settings
from django.utils import timezone

class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="%(class)s_created",)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="%(class)s_updated",)

    class Meta:
        abstract = True
=======
from django.utils import timezone
from django.conf import settings


class BaseModel(models.Model):
    created_at=models.DateTimeField(default=timezone.now,editable=False)
    updated_at=models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="created_by_user")
    updated_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="updated_by_user")

    class Meta:
        abstract=True
>>>>>>> Stashed changes
