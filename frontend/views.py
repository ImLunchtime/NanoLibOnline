from django.shortcuts import render
from books.models import Book
from bundles.models import Bundle

def home(request):
    """Main page view"""
    books = Book.objects.filter(status=Book.Status.NORMAL)
    bundles = Bundle.objects.filter(status=Bundle.Status.NORMAL)
    context = {
        'books': books,
        'bundles': bundles,
    }
    return render(request, 'frontend/home.html', context)
