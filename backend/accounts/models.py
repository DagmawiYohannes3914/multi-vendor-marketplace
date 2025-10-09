# accounts/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_vendor = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)

    def __str__(self):
        return self.username
