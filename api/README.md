# NanoLibOnline API Documentation

## Authentication

The API uses token-based authentication. All requests (except token generation) must include an `Authorization` header with a valid token.

### Obtaining a Token

```http
POST /api-token-auth/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "token": "your_auth_token"
}
```

### Using the Token

Include the token in the Authorization header for all API requests:

```http
Authorization: Token your_auth_token
```

## Endpoints

### Book Profile Management

Book profiles contain metadata shared across multiple copies of the same book.

#### List Book Profiles

```http
GET /api/book-profiles/
Authorization: Token your_auth_token
```

Query Parameters:
- `author`: Filter by author ID
- `series`: Filter by series ID
- `search`: Search in name, ISBN, and description
- `ordering`: Order by name, time_added, or last_updated (prefix with - for descending)

**Response:**
```json
[
    {
        "id": 1,
        "name": "The Great Gatsby",
        "isbn": "9780743273565",
        "description": "A novel by F. Scott Fitzgerald",
        "icon": "/media/book_covers/gatsby.jpg",
        "author": 1,
        "author_details": {
            "id": 1,
            "name": "F. Scott Fitzgerald",
            "description": "American novelist"
        },
        "series": null,
        "series_details": null,
        "time_added": "2024-03-02T10:00:00Z",
        "last_updated": "2024-03-02T10:00:00Z",
        "copies_count": 3
    }
]
```

#### Create Book Profile (Staff Only)

```http
POST /api/book-profiles/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "name": "The Great Gatsby",
    "isbn": "9780743273565",
    "description": "A novel by F. Scott Fitzgerald",
    "author": 1,
    "series": null
}
```

#### Update Book Profile (Staff Only)

```http
PUT /api/book-profiles/{id}/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "name": "The Great Gatsby",
    "isbn": "9780743273565",
    "description": "Updated description",
    "author": 1,
    "series": null
}
```

#### Delete Book Profile (Staff Only)

```http
DELETE /api/book-profiles/{id}/
Authorization: Token your_auth_token
```

### Book Management

Books represent individual copies of book profiles.

#### List Books

```http
GET /api/books/
Authorization: Token your_auth_token
```

Query Parameters:
- `status`: Filter by status (NOR, BOR, BOK, WOF, LOS, BUN)
- `profile`: Filter by book profile ID
- `search`: Search in NL code, profile name, and ISBN
- `ordering`: Order by nl_code, time_added, or last_updated

**Response:**
```json
[
    {
        "id": 1,
        "profile": 1,
        "profile_details": {
            "id": 1,
            "name": "The Great Gatsby",
            "isbn": "9780743273565",
            "description": "A novel by F. Scott Fitzgerald",
            "author_details": {
                "id": 1,
                "name": "F. Scott Fitzgerald",
                "description": "American novelist"
            },
            "series_details": null
        },
        "nl_code": "NL1234",
        "status": "NOR",
        "status_display": "Normal",
        "time_added": "2024-03-02T10:00:00Z",
        "last_updated": "2024-03-02T10:00:00Z",
        "current_borrower": null
    }
]
```

#### Create Book (Staff Only)

```http
POST /api/books/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "profile": 1,
    "nl_code": "NL1234"
}
```

**Note:** NL code must start with "NL" followed by numbers and must be unique.

#### Delete Book (Staff Only)

```http
DELETE /api/books/{id}/
Authorization: Token your_auth_token
```

**Note:** Only books with "Normal" status can be deleted.

#### Write Off Book (Staff Only)

```http
POST /api/books/{id}/write_off/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "status": "success",
    "message": "Book has been written off",
    "book": {
        "id": 1,
        "nl_code": "NL1234",
        "status": "WOF",
        "status_display": "Written Off"
        // ... other book details
    }
}
```

#### Mark Book as Lost (Staff Only)

```http
POST /api/books/{id}/mark_lost/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "status": "success",
    "message": "Book has been marked as lost",
    "book": {
        "id": 1,
        "nl_code": "NL1234",
        "status": "LOS",
        "status_display": "Lost"
        // ... other book details
    }
}
```

### Book Borrowing Management

#### List All Borrow Records

Retrieves a list of all borrowing records.

```http
GET /api/borrowing/
Authorization: Token your_auth_token
```

**Response:**
```json
[
    {
        "id": 1,
        "book": 123,
        "borrower": 456,
        "status": "ACT",
        "status_display": "Active",
        "borrowed_date": "2024-03-02T10:00:00Z",
        "due_date": "2024-04-01T10:00:00Z",
        "returned_date": null,
        "notes": "Sample borrow note",
        "book_title": "The Great Gatsby",
        "borrower_name": "john_doe"
    }
]
```

#### Create a Borrow Record

Creates a new borrow record for a book.

```http
POST /api/borrowing/create_borrow/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "book_id": 123,
    "user_id": 456,
    "notes": "Borrowed for research"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Borrow record created successfully",
    "record": {
        "id": 1,
        "book": 123,
        "borrower": 456,
        "status": "ACT",
        "status_display": "Active",
        "borrowed_date": "2024-03-02T10:00:00Z",
        "due_date": "2024-04-01T10:00:00Z",
        "returned_date": null,
        "notes": "Borrowed for research",
        "book_title": "The Great Gatsby",
        "borrower_name": "john_doe"
    }
}
```

**Possible Errors:**
- 400 Bad Request: Book not found
- 400 Bad Request: User profile not found
- 400 Bad Request: Book is not available for borrowing
- 400 Bad Request: User has reached borrowing limit

#### Return a Book

Processes the return of a borrowed book.

```http
POST /api/borrowing/return_book/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "book_id": 123,
    "notes": "Returned in good condition"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Book returned successfully",
    "record": {
        "id": 1,
        "book": 123,
        "borrower": 456,
        "status": "RET",
        "status_display": "Returned",
        "borrowed_date": "2024-03-02T10:00:00Z",
        "due_date": "2024-04-01T10:00:00Z",
        "returned_date": "2024-03-15T14:30:00Z",
        "notes": "Borrowed for research\nReturn notes: Returned in good condition",
        "book_title": "The Great Gatsby",
        "borrower_name": "john_doe"
    }
}
```

**Possible Errors:**
- 400 Bad Request: Book not found
- 400 Bad Request: No active borrow record found for this book

## Error Responses

The API returns appropriate HTTP status codes and error messages:

- 200: Successful operation
- 201: Resource created successfully
- 400: Bad Request (invalid input, validation errors)
- 401: Unauthorized (missing or invalid authentication)
- 403: Forbidden (insufficient permissions)
- 404: Resource not found
- 500: Internal Server Error

Error responses follow this format:
```json
{
    "status": "error",
    "message": "Error description"
}
```

## Permissions

All endpoints require:
1. Authentication (valid token)
2. Staff privileges (is_staff=True)

## Notes

- All dates are returned in ISO 8601 format with timezone (UTC)
- Book borrowing period is automatically set to 30 days
- The API enforces user borrowing limits as defined in their profile
- Book status is automatically updated when borrowed or returned
- Book profiles can be shared among multiple book copies
- NL codes must be unique and follow the format "NL" followed by numbers
- Books can only be deleted when in "Normal" status
- Book status changes are automatically handled during borrowing/returning 