from django.contrib import admin
from .models import Book, Author, Series

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'nl_code', 'isbn', 'author', 'series', 'status', 'time_added')
    list_filter = ('author', 'series', 'status', 'time_added')
    search_fields = ('name', 'nl_code', 'isbn', 'description')
    readonly_fields = ('time_added', 'last_updated')
    
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
