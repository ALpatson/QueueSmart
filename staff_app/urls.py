from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('availability/', views.availability_calendar, name='staff_availability'),
    path('analytics/', views.staff_analytics_view, name='staff_analytics'),
    path('add-availability/<str:date_str>/', views.add_time_slot, name='add_time_slot'),
    path('delete-availability/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),
    path('toggle-availability/<int:slot_id>/', views.toggle_availability, name='toggle_availability'),
    path('approve/<int:id>/', views.approve_appointment, name='staff_approve'),
    path('reject/<int:id>/', views.reject_appointment, name='staff_reject'),
    path('serving/<int:id>/', views.mark_serving, name='staff_serving'),
    path('complete/<int:id>/', views.complete_appointment, name='staff_complete'),
    path('logout/', views.logout, name='staff_logout'),
]