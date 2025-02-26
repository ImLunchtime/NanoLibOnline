from django.contrib import admin
from .models import BookBorrowing, BundleBorrowing

class BaseBorrowingAdmin(admin.ModelAdmin):
    list_display = (
        'get_item_display',
        'user',
        'borrow_date',
        'due_date',
        'return_date',
        'status',
        'days_overdue'
    )
    list_filter = ('status', 'borrow_date', 'due_date', 'return_date')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('days_overdue',)
    
    def get_item_display(self, obj):
        return str(obj.book if hasattr(obj, 'book') else obj.bundle)
    get_item_display.short_description = 'Item'

@admin.register(BookBorrowing)
class BookBorrowingAdmin(BaseBorrowingAdmin):
    raw_id_fields = ('user', 'book')
    list_filter = BaseBorrowingAdmin.list_filter + ('book__status',)
    search_fields = BaseBorrowingAdmin.search_fields + ('book__name', 'book__nl_code')

@admin.register(BundleBorrowing)
class BundleBorrowingAdmin(BaseBorrowingAdmin):
    raw_id_fields = ('user', 'bundle')
    list_filter = BaseBorrowingAdmin.list_filter + ('bundle__status',)
    search_fields = BaseBorrowingAdmin.search_fields + ('bundle__name', 'bundle__bundle_id')
