from django.contrib import admin
from .models import CustomUser, Service, Appointment, Notification
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Service)        
admin.site.register(Appointment)
admin.site.register(Notification)