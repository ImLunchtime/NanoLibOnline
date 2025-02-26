from django.contrib import admin
from .models import Bundle

@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = (
        'bundle_id', 
        'name', 
        'status', 
        'get_books_count', 
        'get_available_books_count',
        'time_added'
    )
    list_filter = ('status', 'time_added')
    search_fields = ('bundle_id', 'name', 'description')
    filter_horizontal = ('books',)  # Makes it easier to manage many-to-many relationships
    readonly_fields = ('time_added', 'last_updated')
    
    def get_books_count(self, obj):
        return obj.books.count()
    get_books_count.short_description = 'Total Books'
    
    def get_available_books_count(self, obj):
        return obj.available_books_count
    get_available_books_count.short_description = 'Available Books'
