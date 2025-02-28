from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .models import BorrowRecord
from books.models import Book
from users.models import Profile
import json

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def create_borrow(request):
    """Create a new borrow record"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        user_id = data.get('user_id')
        notes = data.get('notes', '')

        if not book_id or not user_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Book ID and User ID are required'
            }, status=400)

        book = get_object_or_404(Book, id=book_id)
        borrower = get_object_or_404(Profile, user_id=user_id)

        # Check if book is available
        if book.status != Book.Status.NORMAL:
            return JsonResponse({
                'status': 'error',
                'message': f'Book is not available for borrowing. Current status: {book.get_status_display()}'
            }, status=400)

        # Check if user has reached borrowing limit
        active_borrows = BorrowRecord.objects.filter(
            borrower=borrower,
            status=BorrowRecord.Status.ACTIVE
        ).count()
        
        if active_borrows >= borrower.borrow_limit:
            return JsonResponse({
                'status': 'error',
                'message': f'User has reached borrowing limit of {borrower.borrow_limit} books'
            }, status=400)

        # Auto-calculate due date (30 days from now)
        due_date = timezone.now() + timedelta(days=30)

        # Create borrow record
        borrow_record = BorrowRecord.objects.create(
            book=book,
            borrower=borrower,
            borrowed_date=timezone.now(),
            due_date=due_date,
            notes=notes,
            status=BorrowRecord.Status.ACTIVE
        )

        # Update book status
        book.status = Book.Status.BORROWED
        book.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Borrow record created successfully',
            'record_id': borrow_record.id,
            'due_date': due_date.strftime('%Y-%m-%d')
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def return_book(request):
    """Return a borrowed book"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        notes = data.get('notes', '')

        if not book_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Book ID is required'
            }, status=400)

        book = get_object_or_404(Book, id=book_id)
        
        # Find active borrow record
        borrow_record = BorrowRecord.objects.filter(
            book=book,
            status=BorrowRecord.Status.ACTIVE
        ).first()
        
        if not borrow_record:
            return JsonResponse({
                'status': 'error',
                'message': 'No active borrow record found for this book'
            }, status=400)

        # Update borrow record
        borrow_record.status = BorrowRecord.Status.RETURNED
        borrow_record.returned_date = timezone.now()
        borrow_record.notes = f"{borrow_record.notes}\nReturn notes: {notes}".strip()
        borrow_record.save()

        # Update book status
        book.status = Book.Status.NORMAL
        book.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Book returned successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
