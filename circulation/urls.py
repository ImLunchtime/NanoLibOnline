from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('borrow/', views.create_borrow, name='create_borrow'),
    path('return/', views.return_book, name='return_book'),
] 