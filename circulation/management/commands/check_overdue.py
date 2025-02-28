from django.core.management.base import BaseCommand
from django.utils import timezone
from circulation.models import BorrowRecord
from books.models import Book

class Command(BaseCommand):
    help = 'Check for overdue books and update their status'

    def handle(self, *args, **options):
        # Get all active borrow records
        active_borrows = BorrowRecord.objects.filter(
            status=BorrowRecord.Status.ACTIVE,
            due_date__lt=timezone.now()
        )
        
        count = 0
        for borrow in active_borrows:
            # Update book status to overdue
            book = borrow.book
            book.status = Book.Status.OVERDUE
            book.save()
            
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} overdue books')
        ) 