from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from subscriptions.models import Subscription
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    
    @property
    def age(self):
        if self.birthday:
            today = date.today()
            return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        return None
    
    @property
    def active_subscription(self):
        """Get the user's active subscription"""
        return self.user.subscriptions.filter(
            status=Subscription.Status.ACTIVE,
            start_date__lte=timezone.now(),
            end_date__gt=timezone.now()
        ).first()
    
    @property
    def has_active_free_plan(self):
        """Check if user has an active free borrowing plan"""
        sub = self.active_subscription
        return sub and sub.free_borrowing_plan is not None
    
    @property
    def has_active_bundle_plan(self):
        """Check if user has an active bundle borrowing plan"""
        sub = self.active_subscription
        return sub and sub.bundle_borrowing_plan is not None
    
    @property
    def max_books_allowed(self):
        """Get maximum number of books user can borrow"""
        sub = self.active_subscription
        return sub.free_borrowing_plan.max_books if sub and sub.free_borrowing_plan else 0
    
    @property
    def max_bundles_allowed(self):
        """Get maximum number of bundles user can borrow"""
        sub = self.active_subscription
        return sub.bundle_borrowing_plan.max_bundles if sub and sub.bundle_borrowing_plan else 0

    @property
    def active_borrows(self):
        """Return all active borrows for this user"""
        return self.borrow_records.filter(status='ACT')
    
    @property
    def borrowed_books(self):
        """Return all currently borrowed books"""
        return [record.book for record in self.active_borrows.filter(book__isnull=False)]
    
    @property
    def borrowed_bundles(self):
        """Return all currently borrowed bundles"""
        return [record.bundle for record in self.active_borrows.filter(bundle__isnull=False)]
    
    def can_borrow(self):
        """Check if user can borrow more items"""
        # Add your business logic here
        max_borrows = 5  # Example limit
        return self.active_borrows.count() < max_borrows
    
    def has_overdue_items(self):
        """Check if user has any overdue items"""
        now = timezone.now()
        return self.borrow_records.filter(
            status='ACT',
            due_date__lt=now
        ).exists()

    def __str__(self):
        return f"{self.user.username}'s profile"

# Signal to create/update Profile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
