from django.contrib import admin
from .models import BookBorrowing, BundleBorrowing, BorrowRecord

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

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = (
        'borrower',
        'book',
        'bundle',
        'status',
        'borrowed_date',
        'due_date',
        'returned_date'
    )
    list_filter = ('status', 'borrowed_date', 'due_date')
    search_fields = (
        'borrower__user__username',
        'book__nl_code',
        'bundle__bundle_id',
        'notes'
    )
    raw_id_fields = ('borrower', 'book', 'bundle')
    date_hierarchy = 'borrowed_date'
    
    actions = ['mark_as_returned', 'mark_as_lost']
    
    def mark_as_returned(self, request, queryset):
        for record in queryset:
            record.mark_as_returned()
    mark_as_returned.short_description = "Mark selected records as returned"
    
    def mark_as_lost(self, request, queryset):
        for record in queryset:
            record.mark_as_lost()
    mark_as_lost.short_description = "Mark selected records as lost"
