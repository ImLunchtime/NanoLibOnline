from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from books.models import Book
from bundles.models import Bundle

class BaseBorrowing(models.Model):
    """Abstract base class for borrowing records"""
    class Status(models.TextChoices):
        PENDING = 'PEN', 'Pending'
        BORROWED = 'BOR', 'Borrowed'
        RETURNED = 'RET', 'Returned'
        OVERDUE = 'OVD', 'Overdue'
        CANCELLED = 'CAN', 'Cancelled'
    
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    borrow_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        abstract = True
        ordering = ['-borrow_date']
    
    def clean(self):
        if self.return_date and self.return_date < self.borrow_date:
            raise ValidationError("Return date cannot be earlier than borrow date")
    
    def save(self, *args, **kwargs):
        # Update status based on dates
        now = timezone.now()
        if self.return_date:
            self.status = self.Status.RETURNED
        elif self.status == self.Status.BORROWED and now > self.due_date:
            self.status = self.Status.OVERDUE
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status in [self.Status.PENDING, self.Status.BORROWED, self.Status.OVERDUE]
    
    @property
    def days_overdue(self):
        if not self.is_active or timezone.now() <= self.due_date:
            return 0
        return (timezone.now() - self.due_date).days

class BookBorrowing(BaseBorrowing):
    """Model for tracking individual book borrowing"""
    book = models.ForeignKey(
        Book, 
        on_delete=models.PROTECT,
        related_name='borrowing_records'
    )
    
    def __str__(self):
        return f"{self.book.name} - {self.user.username} ({self.get_status_display()})"
    
    def clean(self):
        super().clean()
        # Check if book is available
        if self.book.status not in [Book.Status.NORMAL, Book.Status.BOOKED]:
            raise ValidationError("This book is not available for borrowing")
        
        # Check if user has active subscription with free borrowing plan
        if not self.user.profile.has_active_free_plan:
            raise ValidationError("User does not have an active free borrowing plan")
        
        # Check if user has reached their book limit
        if (self.user.profile.max_books_allowed <= 
            BookBorrowing.objects.filter(
                user=self.user,
                status__in=[self.Status.PENDING, self.Status.BORROWED]
            ).count()):
            raise ValidationError("User has reached their maximum book borrowing limit")

class BundleBorrowing(BaseBorrowing):
    """Model for tracking bundle borrowing"""
    bundle = models.ForeignKey(
        Bundle,
        on_delete=models.PROTECT,
        related_name='borrowing_records'
    )
    
    def __str__(self):
        return f"{self.bundle.name} - {self.user.username} ({self.get_status_display()})"
    
    def clean(self):
        super().clean()
        # Check if bundle is available
        if not self.bundle.is_available():
            raise ValidationError("This bundle is not available for borrowing")
        
        # Check if user has active subscription with bundle plan
        if not self.user.profile.has_active_bundle_plan:
            raise ValidationError("User does not have an active bundle borrowing plan")
        
        # Check if user has reached their bundle limit
        if (self.user.profile.max_bundles_allowed <= 
            BundleBorrowing.objects.filter(
                user=self.user,
                status__in=[self.Status.PENDING, self.Status.BORROWED]
            ).count()):
            raise ValidationError("User has reached their maximum bundle borrowing limit")
