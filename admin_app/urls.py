from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.admin_register, name='admin_register'),
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('create-staff/', views.create_staff, name='create_staff'),
    path('logout/', views.logout, name='admin_logout'),
    path('delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]