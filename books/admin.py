from django.contrib import admin
from .models import Book, BookProfile, Author, Series

@admin.register(BookProfile)
class BookProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'isbn', 'author', 'series', 'time_added')
    list_filter = ('author', 'series', 'time_added')
    search_fields = ('name', 'isbn', 'description')
    readonly_fields = ('time_added', 'last_updated')
    raw_id_fields = ('author', 'series')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('nl_code', 'get_name', 'get_author', 'status', 'time_added')
    list_filter = ('status', 'time_added', 'profile__author', 'profile__series')
    search_fields = ('nl_code', 'profile__name', 'profile__isbn')
    readonly_fields = ('time_added', 'last_updated')
    raw_id_fields = ('profile',)
    
    def get_name(self, obj):
        return obj.profile.name
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'profile__name'
    
    def get_author(self, obj):
        return obj.profile.author
    get_author.short_description = 'Author'
    get_author.admin_order_field = 'profile__author'

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
