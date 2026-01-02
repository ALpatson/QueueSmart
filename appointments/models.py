from django.db import models
from django.contrib.auth.models import User

class CustomUser(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('staff', 'Staff'),('client', 'Client')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.last_name + ", " + self.first_name
    
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField()
    staff = models.ManyToManyField(CustomUser, related_name='services')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        ordering = ['name']
        
class Appointment(models.Model):
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    # ✅ ADD THIS FIELD - Track which staff member handles this appointment
    staff = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='staff_appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),('serving', 'Serving'), ('completed', 'Completed')], default='pending')
    queue_number = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.first_name} - {self.service.name} - {self.appointment_date}"
    
    class Meta:
        ordering = ['-created_at']
        
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('confirmation', 'Confirmation'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('reminder', 'Reminder'),
        ('cancellation', 'Cancellation'),
        ('edited', 'Edited'),
        ('booking', 'Booking'),  # ✅ ADD THIS for staff new booking notifications
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, related_name='notifications', blank=True, null=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='confirmation')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"
    
    class Meta:
        ordering = ['-sent_at']
        
class StaffAvailability(models.Model):
    staff = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        verbose_name_plural = "Staff Availabilities"
    
    def __str__(self):
        status = "Available" if self.is_available else "Occupied"
        return f"{self.staff.first_name} - {self.date} ({self.start_time}-{self.end_time}) ({status})"