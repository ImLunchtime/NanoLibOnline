from django.urls import path
from . import views

app_name = 'bundles'

urlpatterns = [
    path('', views.bundle_list, name='bundle_list'),
    path('<int:pk>/', views.bundle_detail, name='bundle_detail'),
] 