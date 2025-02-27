from django.db import models
from django.core.validators import RegexValidator

class Author(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Series(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "series"  # Fix plural form in admin
    
    def __str__(self):
        return self.name

class BookProfile(models.Model):
    """Model for book metadata that can be shared across multiple copies"""
    name = models.CharField(max_length=200)
    isbn = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="ISBN"
    )
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='book_profiles'
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='book_profiles'
    )
    
    # Metadata
    time_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.isbn})"

class Book(models.Model):
    """Model for individual book copies"""
    class Status(models.TextChoices):
        NORMAL = 'NOR', 'Normal'
        BORROWED = 'BOR', 'Borrowed'
        BOOKED = 'BOK', 'Booked'
        WRITTEN_OFF = 'WOF', 'Written Off'
        IN_BUNDLE = 'BUN', 'In Bundle'
    
    profile = models.ForeignKey(
        BookProfile,
        on_delete=models.PROTECT,
        related_name='copies'
    )
    nl_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex='^NL\d+$',
                message='NL code must start with NL followed by numbers',
            )
        ],
        verbose_name="NL Code"
    )
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.NORMAL,
    )
    
    # Metadata
    time_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nl_code']
    
    def __str__(self):
        return f"{self.profile.name} ({self.nl_code}) - {self.get_status_display()}"
    
    @property
    def name(self):
        return self.profile.name
    
    @property
    def isbn(self):
        return self.profile.isbn
    
    @property
    def description(self):
        return self.profile.description
    
    @property
    def author(self):
        return self.profile.author
    
    @property
    def series(self):
        return self.profile.series
