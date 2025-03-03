from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'borrowing', views.BorrowingViewSet, basename='borrowing')
router.register(r'books', views.BookViewSet, basename='books')
router.register(r'book-profiles', views.BookProfileViewSet, basename='book-profiles')

urlpatterns = [
    path('', include(router.urls)),
] 