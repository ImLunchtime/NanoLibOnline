from django.db import models
from django.core.validators import RegexValidator
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from books.models import Book

class Bundle(models.Model):
    class Status(models.TextChoices):
        NORMAL = 'NOR', 'Normal'
        BORROWED = 'BOR', 'Borrowed'
        PREPARING = 'PRE', 'Preparing'
        LOST = 'LOS', 'Lost'
    
    # Required fields
    bundle_id = models.CharField(
        max_length=10,
        unique=True,
        # validators=[
        #     RegexValidator(
        #         regex='^[A-Z]\d+$',
        #         message='Bundle ID must be a letter followed by numbers (e.g., A12)',
        #     )
        # ],
        verbose_name="Bundle ID"
    )
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.NORMAL,
    )
    
    # Optional fields
    description = models.TextField(blank=True)
    books = models.ManyToManyField(
        Book,
        related_name='bundles',
        blank=True
    )
    
    # Metadata
    time_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['bundle_id']
    
    def __str__(self):
        return f"{self.bundle_id} - {self.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Convert bundle_id to uppercase
        self.bundle_id = self.bundle_id.upper()
        super().save(*args, **kwargs)

    def update_books_status(self):
        """Update the status of all books in the bundle"""
        # Set all current books to IN_BUNDLE status
        self.books.all().update(status=Book.Status.IN_BUNDLE)
    
    def remove_books_status(self, books_to_remove=None):
        """Reset the status of removed books to NORMAL"""
        if books_to_remove is None:
            books_to_remove = self.books.all()
        
        # Only update books that aren't in any other bundles
        for book in books_to_remove:
            if book.bundles.count() <= 1:  # 1 because the current bundle is still counted
                book.status = Book.Status.NORMAL
                book.save()

    def add_books(self, books):
        """
        Add books to the bundle and update their status
        Args:
            books: A single Book instance or a list of Book instances
        """
        if not isinstance(books, (list, tuple)):
            books = [books]
        
        # Filter out books that are borrowed or written off
        valid_books = [
            book for book in books 
            if book.status not in [Book.Status.BORROWED, Book.Status.WRITTEN_OFF]
        ]
        
        if valid_books:
            self.books.add(*valid_books)
    
    def remove_books(self, books):
        """
        Remove books from the bundle
        Args:
            books: A single Book instance or a list of Book instances
        """
        if not isinstance(books, (list, tuple)):
            books = [books]
        
        self.books.remove(*books)
    
    def clear_books(self):
        """Remove all books from the bundle"""
        self.books.clear()
    
    @property
    def available_books_count(self):
        """Return the count of books that are actually available"""
        return self.books.filter(status=Book.Status.IN_BUNDLE).count()
    
    def is_available(self):
        """Check if the bundle is available for borrowing"""
        return (
            self.status == self.Status.NORMAL and 
            self.books.exists() and 
            self.available_books_count == self.books.count()
        )

@receiver(m2m_changed, sender=Bundle.books.through)
def handle_bundle_books_changed(sender, instance, action, pk_set, **kwargs):
    """Signal handler for when books are added to or removed from a bundle"""
    if action == "post_add":
        # Update status for newly added books
        instance.update_books_status()
    
    elif action == "pre_remove":
        # Get the books that are about to be removed
        books_to_remove = Book.objects.filter(pk__in=pk_set)
        instance.remove_books_status(books_to_remove)
    
    elif action == "post_clear":
        # Handle clearing all books from bundle
        instance.remove_books_status()
