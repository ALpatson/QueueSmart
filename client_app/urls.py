from django.urls import path
from . import views
from appointments.models import Notification

urlpatterns = [
    path('register/', views.client_register, name='client_register'),
    path('login/', views.client_login, name='client_login'),
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('book/', views.book_appointment, name='client_book'),
    path('logout/', views.logout, name='client_logout'),
    path('edit/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('analytics/', views.client_analytics_view, name='client_analytics'),
]