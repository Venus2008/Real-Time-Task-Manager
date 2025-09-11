from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from Backend.models import BaseModel

ROLE_CHOICES = (
    ('ADMIN', 'ADMIN'),
    ('MANAGER', 'MANAGER'),
    ('EMPLOYEE', 'EMPLOYEE'),
)

class UserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError("Email is required")
        email=self.normalize_email(email)
        user=self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,email,password=None,**extra_fields):
        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)
        extra_fields.setdefault("role","ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email,password,**extra_fields)  
    
class User(AbstractUser,BaseModel):
    username=None
    name=models.CharField(max_length=100)
    email=models.EmailField(unique=True)
    role=models.CharField(choices=ROLE_CHOICES,max_length=20,default='EMPLOYEE')
    

    
    objects=UserManager()

    USERNAME_FIELD="email"
    REQUIRED_FIELDS=["name"]

    def __str__(self):
        return f"{self.name} ({self.role})"


