from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class PlanDuration(models.Model):
    """Model to store different subscription durations"""
    months = models.PositiveIntegerField(unique=True)
    description = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['months']
    
    def __str__(self):
        return f"{self.months} month{'s' if self.months > 1 else ''}"

class BasePlan(models.Model):
    """Abstract base class for subscription plans"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.ForeignKey(PlanDuration, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        ordering = ['duration', 'price']
    
    def __str__(self):
        return f"{self.name} ({self.duration})"

class FreeBorrowingPlan(BasePlan):
    """Plan for borrowing individual books"""
    max_books = models.PositiveIntegerField(help_text="Maximum number of books that can be borrowed simultaneously")
    
    class Meta(BasePlan.Meta):
        verbose_name = "Free Borrowing Plan"
        verbose_name_plural = "Free Borrowing Plans"

class BundleBorrowingPlan(BasePlan):
    """Plan for borrowing book bundles"""
    max_bundles = models.PositiveIntegerField(help_text="Maximum number of bundles that can be borrowed simultaneously")
    
    class Meta(BasePlan.Meta):
        verbose_name = "Bundle Borrowing Plan"
        verbose_name_plural = "Bundle Borrowing Plans"

class Subscription(models.Model):
    """Model to track user subscriptions"""
    class Status(models.TextChoices):
        ACTIVE = 'ACT', 'Active'
        EXPIRED = 'EXP', 'Expired'
        CANCELLED = 'CAN', 'Cancelled'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    free_borrowing_plan = models.ForeignKey(
        FreeBorrowingPlan, 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    bundle_borrowing_plan = models.ForeignKey(
        BundleBorrowingPlan,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        plans = []
        if self.free_borrowing_plan:
            plans.append("Free")
        if self.bundle_borrowing_plan:
            plans.append("Bundle")
        return f"{self.user.username} - {'+'.join(plans)} ({self.get_status_display()})"
    
    def clean(self):
        if not (self.free_borrowing_plan or self.bundle_borrowing_plan):
            raise ValidationError("At least one plan type must be selected")
        
        # Calculate end_date based on the longest duration of selected plans
        months = 0
        if self.free_borrowing_plan:
            months = max(months, self.free_borrowing_plan.duration.months)
        if self.bundle_borrowing_plan:
            months = max(months, self.bundle_borrowing_plan.duration.months)
        
        if not self.end_date:  # Only set if not manually specified
            self.end_date = self.start_date + relativedelta(months=months)
        
        # Check for overlapping active subscriptions
        overlapping = Subscription.objects.filter(
            user=self.user,
            status=self.Status.ACTIVE,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        if self.pk:  # Exclude current subscription when updating
            overlapping = overlapping.exclude(pk=self.pk)
        
        if overlapping.exists():
            raise ValidationError("User already has an active subscription during this period")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return (
            self.status == self.Status.ACTIVE and
            self.start_date <= timezone.now() <= self.end_date
        )
