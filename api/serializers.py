from rest_framework import serializers
from circulation.models import BorrowRecord
from books.models import Book, BookProfile, Author, Series
from users.models import Profile

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'description']

class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Series
        fields = ['id', 'name', 'description']

class BookProfileSerializer(serializers.ModelSerializer):
    author_details = AuthorSerializer(source='author', read_only=True)
    series_details = SeriesSerializer(source='series', read_only=True)
    copies_count = serializers.SerializerMethodField()

    class Meta:
        model = BookProfile
        fields = [
            'id', 'name', 'isbn', 'description', 'icon',
            'author', 'author_details', 'series', 'series_details',
            'time_added', 'last_updated', 'copies_count'
        ]
        read_only_fields = ['time_added', 'last_updated']

    def get_copies_count(self, obj):
        return obj.copies.count()

class BookSerializer(serializers.ModelSerializer):
    profile_details = BookProfileSerializer(source='profile', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_borrower = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'profile', 'profile_details', 'nl_code',
            'status', 'status_display', 'time_added',
            'last_updated', 'current_borrower'
        ]
        read_only_fields = ['time_added', 'last_updated']

    def get_current_borrower(self, obj):
        active_borrow = obj.borrow_records.filter(status=BorrowRecord.Status.ACTIVE).first()
        if active_borrow:
            return {
                'id': active_borrow.borrower.user.id,
                'username': active_borrow.borrower.user.username,
                'due_date': active_borrow.due_date
            }
        return None

class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['profile', 'nl_code']

    def validate_nl_code(self, value):
        if Book.objects.filter(nl_code=value).exists():
            raise serializers.ValidationError("This NL code is already in use.")
        return value

class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.profile.name', read_only=True)
    borrower_name = serializers.CharField(source='borrower.user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BorrowRecord
        fields = [
            'id', 'book', 'borrower', 'status', 'status_display',
            'borrowed_date', 'due_date', 'returned_date', 'notes',
            'book_title', 'borrower_name'
        ]
        read_only_fields = ['borrowed_date', 'status', 'returned_date']

class BorrowCreateSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        book_id = data.get('book_id')
        user_id = data.get('user_id')

        try:
            book = Book.objects.get(id=book_id)
            borrower = Profile.objects.get(user_id=user_id)
        except Book.DoesNotExist:
            raise serializers.ValidationError({"book_id": "Book not found"})
        except Profile.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User profile not found"})

        if book.status != Book.Status.NORMAL:
            raise serializers.ValidationError(
                {"book_id": f"Book is not available for borrowing. Current status: {book.get_status_display()}"}
            )

        active_borrows = BorrowRecord.objects.filter(
            borrower=borrower,
            status=BorrowRecord.Status.ACTIVE
        ).count()

        if active_borrows >= borrower.borrow_limit:
            raise serializers.ValidationError(
                {"user_id": f"User has reached borrowing limit of {borrower.borrow_limit} books"}
            )

        return data

class ReturnBookSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True) 