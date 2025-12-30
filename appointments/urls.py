from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.registration, name='registration'),
    path('login/', views.login, name='login'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('appointment/<int:appointment_id>/approve/', views.approve_appointment, name='approve_appointment'),
    path('appointment/<int:appointment_id>/reject/', views.reject_appointment, name='reject_appointment'),
    path('appointment/<int:appointment_id>/serving/', views.mark_serving, name='mark_serving'),
]