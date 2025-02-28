from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """Handle profile creation and updates for users"""
    if created:
        # Only create profile for new users
        Profile.objects.get_or_create(user=instance) 