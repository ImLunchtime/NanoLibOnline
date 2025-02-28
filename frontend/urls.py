from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/', views.staff_home, name='staff_home'),
    path('staff/borrow/', views.staff_borrow, name='staff_borrow'),
    path('staff/books/', views.staff_books, name='staff_books'),
    path('staff/return/', views.staff_return, name='staff_return'),
    path('staff/books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('staff/books/<int:book_id>/update/', views.book_update, name='book_update'),
    # API endpoints
    path('api/books/search/', views.search_books, name='search_books'),
    path('api/users/search/', views.search_users, name='search_users'),
] 