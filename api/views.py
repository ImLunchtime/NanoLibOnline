from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from circulation.models import BorrowRecord
from books.models import Book, BookProfile
from users.models import Profile
from .serializers import (
    BorrowRecordSerializer, BorrowCreateSerializer, ReturnBookSerializer,
    BookSerializer, BookProfileSerializer, BookCreateSerializer
)

class BookProfileViewSet(viewsets.ModelViewSet):
    queryset = BookProfile.objects.all()
    serializer_class = BookProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'series']
    search_fields = ['name', 'isbn', 'description']
    ordering_fields = ['name', 'time_added', 'last_updated']

    def get_permissions(self):
        """
        Only staff can create/update/delete book profiles
        Regular users can only view
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'profile']
    search_fields = ['nl_code', 'profile__name', 'profile__isbn']
    ordering_fields = ['nl_code', 'time_added', 'last_updated']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookCreateSerializer
        return BookSerializer

    def get_permissions(self):
        """
        Only staff can create/update/delete books
        Regular users can only view
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        book = self.get_object()
        if book.status != Book.Status.NORMAL:
            return Response({
                'status': 'error',
                'message': f'Cannot delete book with status: {book.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def write_off(self, request, pk=None):
        """Mark a book as written off"""
        book = self.get_object()
        if book.status != Book.Status.NORMAL:
            return Response({
                'status': 'error',
                'message': f'Cannot write off book with status: {book.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        book.status = Book.Status.WRITTEN_OFF
        book.save()
        return Response({
            'status': 'success',
            'message': 'Book has been written off',
            'book': BookSerializer(book).data
        })

    @action(detail=True, methods=['post'])
    def mark_lost(self, request, pk=None):
        """Mark a book as lost"""
        book = self.get_object()
        if book.status not in [Book.Status.BORROWED, Book.Status.NORMAL]:
            return Response({
                'status': 'error',
                'message': f'Cannot mark book as lost with status: {book.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # If book was borrowed, update the borrow record
        active_borrow = book.borrow_records.filter(status=BorrowRecord.Status.ACTIVE).first()
        if active_borrow:
            active_borrow.status = BorrowRecord.Status.LOST
            active_borrow.save()

        book.status = Book.Status.LOST
        book.save()
        return Response({
            'status': 'success',
            'message': 'Book has been marked as lost',
            'book': BookSerializer(book).data
        })

class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create_borrow':
            return BorrowCreateSerializer
        elif self.action == 'return_book':
            return ReturnBookSerializer
        return BorrowRecordSerializer

    @action(detail=False, methods=['post'])
    def create_borrow(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        book = get_object_or_404(Book, id=serializer.validated_data['book_id'])
        borrower = get_object_or_404(Profile, user_id=serializer.validated_data['user_id'])
        notes = serializer.validated_data.get('notes', '')

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

        return Response({
            'status': 'success',
            'message': 'Borrow record created successfully',
            'record': BorrowRecordSerializer(borrow_record).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def return_book(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        book = get_object_or_404(Book, id=serializer.validated_data['book_id'])
        notes = serializer.validated_data.get('notes', '')

        # Find active borrow record
        borrow_record = BorrowRecord.objects.filter(
            book=book,
            status=BorrowRecord.Status.ACTIVE
        ).first()
        
        if not borrow_record:
            return Response({
                'status': 'error',
                'message': 'No active borrow record found for this book'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update borrow record
        borrow_record.status = BorrowRecord.Status.RETURNED
        borrow_record.returned_date = timezone.now()
        borrow_record.notes = f"{borrow_record.notes}\nReturn notes: {notes}".strip()
        borrow_record.save()

        # Update book status
        book.status = Book.Status.NORMAL
        book.save()

        return Response({
            'status': 'success',
            'message': 'Book returned successfully',
            'record': BorrowRecordSerializer(borrow_record).data
        })
