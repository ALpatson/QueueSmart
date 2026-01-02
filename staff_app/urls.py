from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('analytics/', views.staff_analytics_view, name='staff_analytics'),
    
    # Appointment management
    path('approve/<int:id>/', views.approve_appointment, name='staff_approve'),
    path('reject/<int:id>/', views.reject_appointment, name='staff_reject'),
    path('serving/<int:id>/', views.mark_serving, name='staff_serving'),
    path('complete/<int:id>/', views.complete_appointment, name='staff_complete'),
    
    # Availability management (NEW SIMPLE VERSION)
    path('manage-availability/', views.manage_availability, name='staff_manage_availability'),
    path('add-availability/', views.add_availability, name='staff_add_availability'),
    path('delete-availability/', views.delete_availability, name='staff_delete_availability'),
    
    # Auth
    path('logout/', views.logout, name='staff_logout'),
    path('change-password/', views.change_password, name='staff_change_password'),
]