from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-as-read/', views.mark_notifications_as_read, name='mark_as_read'),  # NEW
]