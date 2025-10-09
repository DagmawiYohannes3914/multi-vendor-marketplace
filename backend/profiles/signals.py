from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import VendorProfile, CustomerProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_vendor:
            VendorProfile.objects.create(user=instance, store_name=instance.username)
        elif instance.is_customer:
            CustomerProfile.objects.create(user=instance)
