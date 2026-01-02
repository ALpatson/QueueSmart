from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from appointments.models import Notification, Appointment, CustomUser
from datetime import datetime, timedelta
import json

def send_email_notification(recipient_email, subject, message_text):
    """Send email notification to user"""
    try:
        send_mail(
            subject,
            message_text,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def create_notification(user, appointment, notification_type, message):
    """Create and send both in-app and email notification"""
    # Create in-app notification
    notification = Notification.objects.create(
        user=user,
        appointment=appointment,
        message=message,
        notification_type=notification_type
    )
    
    # Send email
    subject = f"QueueSmart - Appointment {notification_type.title()}"
    email_message = f"""
Hello {user.first_name},

{message}

Appointment Details:
- Service: {appointment.service.name}
- Date: {appointment.appointment_date.strftime('%B %d, %Y')}
- Time: {appointment.appointment_time.strftime('%H:%M')}
- Status: {appointment.status.upper()}
{f"- Queue Number: #{appointment.queue_number}" if appointment.queue_number else ""}

Please log in to QueueSmart for more details.

Thank you for using QueueSmart!
Best regards,
QueueSmart Team
    """
    
    send_email_notification(user.email, subject, email_message)
    return notification

def notify_appointment_booked(appointment):
    """Send notification when appointment is booked"""
    # Notify client
    message = f"Your appointment for {appointment.service.name} on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')} has been booked. We will notify you when it's confirmed."
    
    create_notification(
        appointment.client,
        appointment,
        'confirmation',
        message
    )
    
    # ✅ ALSO NOTIFY STAFF
    notify_staff_new_booking(appointment)


def notify_appointment_approved(appointment):
    """Send notification when appointment is approved"""
    message = f"Great news! Your appointment for {appointment.service.name} has been approved!"
    if appointment.queue_number:
        message += f" Your queue number is #{appointment.queue_number}"
    
    create_notification(
        appointment.client,
        appointment,
        'approval',
        message
    )

def notify_appointment_rejected(appointment):
    """Send notification when appointment is rejected"""
    message = f"Unfortunately, your appointment for {appointment.service.name} on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')} has been rejected. Please book another time slot."
    
    create_notification(
        appointment.client,
        appointment,
        'rejection',
        message
    )

def notify_appointment_serving(appointment):
    """Send notification when it's customer's turn to be served"""
    message = f"It's your turn! Queue #{appointment.queue_number} is now being served for {appointment.service.name}. Please come to the counter."
    
    create_notification(
        appointment.client,
        appointment,
        'reminder',
        message
    )

def notify_appointment_completed(appointment):
    """Send notification when appointment is completed"""
    message = f"Your appointment for {appointment.service.name} has been completed. Thank you for visiting!"
    
    create_notification(
        appointment.client,
        appointment,
        'confirmation',
        message
    )

# ============================================
# ✅ STAFF NOTIFICATION FUNCTIONS
# ============================================

def notify_staff_new_booking(appointment):
    """Notify staff when a client books an appointment"""
    try:
        # Get the staff member assigned to this appointment
        staff = CustomUser.objects.get(id=appointment.staff_id)
        
        client_name = f"{appointment.client.first_name} {appointment.client.last_name}"
        message = f"📌 New booking from {client_name} for {appointment.service.name} on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')}"
        
        # Create in-app notification for staff
        Notification.objects.create(
            user=staff,
            appointment=appointment,
            message=message,
            notification_type='booking'
        )
        
        # Send email to staff
        try:
            email_message = f"""
Hello {staff.first_name},

You have a new appointment booking!

Client: {client_name}
Service: {appointment.service.name}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%H:%M')}
Status: Pending Approval

Please log in to your dashboard to approve or reject this booking.

Best regards,
QueueSmart Team
            """
            
            send_email_notification(
                staff.email,
                f'QueueSmart - New Appointment Booking',
                email_message
            )
        except Exception as e:
            print(f"Error sending email to staff: {e}")
    except CustomUser.DoesNotExist:
        print(f"Staff with id {appointment.staff_id} not found")
    except Exception as e:
        print(f"Error notifying staff of new booking: {str(e)}")


def notify_staff_appointment_cancelled(appointment):
    """Notify staff when a client cancels an appointment"""
    try:
        # Get the staff member assigned to this appointment
        staff = CustomUser.objects.get(id=appointment.staff_id)
        
        client_name = f"{appointment.client.first_name} {appointment.client.last_name}"
        message = f"❌ Appointment cancelled: {client_name} cancelled their booking for {appointment.service.name} on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')}. Time slot is now available."
        
        # Create in-app notification for staff
        Notification.objects.create(
            user=staff,
            appointment=appointment,
            message=message,
            notification_type='cancellation'
        )
        
        # Send email to staff
        try:
            email_message = f"""
Hello {staff.first_name},

An appointment has been cancelled.

Client: {client_name}
Service: {appointment.service.name}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%H:%M')}

Your time slot is now available again.

Best regards,
QueueSmart Team
            """
            
            send_email_notification(
                staff.email,
                f'QueueSmart - Appointment Cancelled',
                email_message
            )
        except Exception as e:
            print(f"Error sending email to staff: {e}")
    except CustomUser.DoesNotExist:
        print(f"Staff with id {appointment.staff_id} not found")
    except Exception as e:
        print(f"Error notifying staff of cancellation: {str(e)}")


def notify_staff_appointment_edited(appointment, old_date, old_time):
    """Notify staff when a client edits their appointment"""
    try:
        # Get the staff member assigned to this appointment
        staff = CustomUser.objects.get(id=appointment.staff_id)
        
        client_name = f"{appointment.client.first_name} {appointment.client.last_name}"
        message = f"✏️ Appointment modified: {client_name} changed their {appointment.service.name} appointment from {old_date.strftime('%B %d, %Y')} at {old_time.strftime('%H:%M')} to {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')}"
        
        # Create in-app notification for staff
        Notification.objects.create(
            user=staff,
            appointment=appointment,
            message=message,
            notification_type='edited'
        )
        
        # Send email to staff
        try:
            email_message = f"""
Hello {staff.first_name},

An appointment has been modified.

Client: {client_name}
Service: {appointment.service.name}
Old Time: {old_date.strftime('%B %d, %Y')} at {old_time.strftime('%H:%M')}
New Time: {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%H:%M')}

Please update your schedule accordingly.

Best regards,
QueueSmart Team
            """
            
            send_email_notification(
                staff.email,
                f'QueueSmart - Appointment Modified',
                email_message
            )
        except Exception as e:
            print(f"Error sending email to staff: {e}")
    except CustomUser.DoesNotExist:
        print(f"Staff with id {appointment.staff_id} not found")
    except Exception as e:
        print(f"Error notifying staff of edit: {str(e)}")


def get_staff_unread_notifications(user_id):
    """Get count of unread notifications for staff"""
    return Notification.objects.filter(user_id=user_id, is_read=False).count()


def view_notifications(request):
    """View all notifications for logged in user"""
    if request.session.get('user_role') not in ['client', 'staff']:
        return redirect('client_login')
    
    user_id = request.session.get('user_id')
    notifications = Notification.objects.filter(user_id=user_id).order_by('-sent_at')
    
    # Mark all as read when viewing
    Notification.objects.filter(user_id=user_id, is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'notifications/view.html', context)

@require_POST
def mark_notifications_as_read(request):
    """Mark all notifications as read for logged in user"""
    if request.session.get('user_role') not in ['client', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=403)
    
    user_id = request.session.get('user_id')
    
    try:
        # Mark all unread notifications as read
        updated_count = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'status': 'success',
            'message': f'{updated_count} notifications marked as read'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def delete_notification(request, notification_id):
    """Delete a notification"""
    if request.session.get('user_role') not in ['client', 'staff']:
        return redirect('client_login')
    
    user_id = request.session.get('user_id')
    
    try:
        notification = Notification.objects.get(id=notification_id, user_id=user_id)
        notification.delete()
        messages.success(request, 'Notification deleted')
    except:
        messages.error(request, 'Notification not found')
    
    return redirect('view_notifications')