from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from .models import VendorProfile, CustomerProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.is_vendor and not hasattr(instance, 'vendor_profile'):
                VendorProfile.objects.create(user=instance, store_name=instance.username)
            if instance.is_customer and not hasattr(instance, 'customer_profile'):
                CustomerProfile.objects.create(user=instance)
        except IntegrityError:
            pass  # Avoid crashing if profiles already exist
