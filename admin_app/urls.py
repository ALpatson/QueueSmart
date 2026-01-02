from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.admin_register, name='admin_register'),
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('create-staff/', views.create_staff, name='admin_create_staff'),  
    path('logout/', views.logout, name='admin_logout'),
    path('delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('create-service/', views.create_service, name='admin_create_service'),
    path('edit-staff/<int:staff_id>/', views.edit_staff, name='admin_edit_staff'),
    path('reset-staff-password/<int:staff_id>/', views.reset_staff_password, name='reset_staff_password'),
    path('edit-service/<int:service_id>/', views.edit_service, name='admin_edit_service'),
    path('delete-service/<int:service_id>/', views.delete_service, name='admin_delete_service'),
    path('forgot-password/', views.forgot_password, name='admin_forgot_password'),
]