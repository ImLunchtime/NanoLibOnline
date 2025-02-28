from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from books.models import Book, Author, Series
from bundles.models import Bundle
from blog.models import Post, Category
from circulation.models import BorrowRecord
import json
from datetime import datetime, timedelta

def home(request):
    """Main page view"""
    featured_post = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).first()
    
    posts = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by('-published')[:6]  # Get latest 6 posts
    
    categories = Category.objects.all()
    
    context = {
        'featured_post': featured_post,
        'posts': posts,
        'categories': categories,
    }
    return render(request, 'frontend/home.html', context)

def is_staff(user):
    return user.is_staff

def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('frontend:staff_home')
        return redirect('frontend:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            if user.is_staff:
                return redirect('frontend:staff_home')
            return redirect('frontend:home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'frontend/login.html', {'form': form})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'Successfully logged out!')
    return redirect('frontend:home')

@login_required
@user_passes_test(is_staff)
def staff_home(request):
    """Staff dashboard view"""
    context = {
        'active_borrows_count': BorrowRecord.objects.filter(status=BorrowRecord.Status.ACTIVE).count(),
        'overdue_count': BorrowRecord.objects.filter(
            status=BorrowRecord.Status.ACTIVE,
            due_date__lt=timezone.now()
        ).count(),
        'recent_records': BorrowRecord.objects.all()[:10]
    }
    return render(request, 'frontend/staff/home.html', context)

@login_required
@user_passes_test(is_staff)
def staff_borrow(request):
    """Book borrowing page"""
    # Calculate due date (30 days from now)
    due_date = timezone.now() + timedelta(days=30)
    return render(request, 'frontend/staff/borrow.html', {
        'due_date': due_date
    })

@login_required
@user_passes_test(is_staff)
def staff_return(request):
    """Book return page"""
    recent_returns = BorrowRecord.objects.filter(
        status=BorrowRecord.Status.RETURNED
    ).select_related(
        'book', 'book__profile', 'borrower', 'borrower__user'
    ).order_by('-returned_date')[:10]
    
    return render(request, 'frontend/staff/return.html', {
        'recent_returns': recent_returns
    })

@login_required
@user_passes_test(is_staff)
def staff_books(request):
    """Book management page"""
    books = Book.objects.select_related('profile').all()
    
    # Apply search filter
    search = request.GET.get('search', '')
    if search:
        books = books.filter(nl_code__icontains=search)
    
    # Apply status filter
    status = request.GET.get('status', '')
    if status:
        books = books.filter(status=status)
    
    # Annotate books with current borrow info
    for book in books:
        book.current_borrow = book.borrow_records.filter(
            status=BorrowRecord.Status.ACTIVE
        ).first()
    
    return render(request, 'frontend/staff/books.html', {'books': books})

@login_required
@user_passes_test(is_staff)
def search_books(request):
    """API endpoint for searching books by NL code"""
    query = request.GET.get('nl_code', '')
    if not query:
        return JsonResponse({'books': []})
    
    books = Book.objects.select_related('profile').filter(
        nl_code__icontains=query
    )[:10]
    
    books_data = [{
        'id': book.id,
        'nl_code': book.nl_code,
        'title': book.profile.name,
        'author': book.profile.author.name,
        'status': book.get_status_display()
    } for book in books]
    
    return JsonResponse({'books': books_data})

@login_required
@user_passes_test(is_staff)
def search_users(request):
    """API endpoint for searching users"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
    } for user in users]
    
    return JsonResponse({'users': users_data})

@login_required
@user_passes_test(is_staff)
def book_detail(request, book_id):
    """Book detail view"""
    book = get_object_or_404(Book, id=book_id)
    borrow_history = book.borrow_records.select_related(
        'borrower', 'borrower__user'
    ).order_by('-borrowed_date')
    
    # Get all authors and series for dropdowns
    authors = Author.objects.all()
    series = Series.objects.all()
    
    # Check if book is currently borrowed
    is_borrowed = book.status in [Book.Status.BORROWED, Book.Status.OVERDUE]
    
    return render(request, 'frontend/staff/book_detail.html', {
        'book': book,
        'borrow_history': borrow_history,
        'authors': authors,
        'series': series,
        'is_borrowed': is_borrowed,
        'book_statuses': Book.Status.choices
    })

@login_required
@user_passes_test(is_staff)
def book_update(request, book_id):
    """Update book details"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        book = get_object_or_404(Book, id=book_id)
        data = json.loads(request.body)
        
        # Update book profile
        profile = book.profile
        profile.name = data.get('title', profile.name)  # Fixed: using name instead of title
        
        # Handle author (foreign key)
        author_id = data.get('author_id')
        if author_id:
            try:
                profile.author = Author.objects.get(id=author_id)
            except Author.DoesNotExist:
                return JsonResponse({'error': 'Author not found'}, status=400)
        
        # Handle series (foreign key)
        series_id = data.get('series_id')
        if series_id:
            try:
                profile.series = Series.objects.get(id=series_id)
            except Series.DoesNotExist:
                return JsonResponse({'error': 'Series not found'}, status=400)
        elif series_id == '':  # Empty string means remove series
            profile.series = None
            
        profile.isbn = data.get('isbn', profile.isbn)
        profile.description = data.get('description', profile.description)
        profile.publisher = data.get('publisher', profile.publisher)
        profile.publication_year = data.get('publication_year', profile.publication_year)
        profile.language = data.get('language', profile.language)
        
        # Handle numeric field
        try:
            if 'pages' in data and data['pages']:
                profile.pages = int(data['pages'])
        except ValueError:
            return JsonResponse({'error': 'Pages must be a number'}, status=400)
            
        profile.save()
        
        # Update book status if not borrowed
        status = data.get('status')
        if status and book.status not in [Book.Status.BORROWED, Book.Status.OVERDUE]:
            book.status = status
            book.save()
        
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
