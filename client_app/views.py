from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from appointments.models import CustomUser, Service, Appointment, StaffAvailability, Notification
from datetime import datetime
import json
from django.db.models import Count
from datetime import date
from notifications.views import (
    notify_appointment_booked,
    notify_appointment_cancelled,
    notify_appointment_edited
)

def client_register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, "Passwords don't match!")
            return redirect('client_register')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('client_register')
        
        CustomUser.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            password=make_password(password),
            role='client'
        )
        messages.success(request, "Account created! Now login.")
        return redirect('client_login')
    
    return render(request, 'client_app/register.html')

def client_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = CustomUser.objects.get(email=email, role='client')
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = 'client'
                return redirect('client_dashboard')
            else:
                messages.error(request, "Invalid password!")
        except CustomUser.DoesNotExist:
            messages.error(request, "Client account not found!")
        
        return redirect('client_login')
    
    return render(request, 'client_app/login.html')

def logout(request):
    request.session.flush()
    return redirect('client_login')

def get_user_context(user_id):
    """Get user context for all views"""
    try:
        user = CustomUser.objects.get(id=user_id)
        return {
            'user_first_name': user.first_name,
            'user_last_name': user.last_name,
        }
    except:
        return {
            'user_first_name': 'User',
            'user_last_name': '',
        }

def client_dashboard(request):
    if request.session.get('user_role') != 'client':
        return redirect('client_login')
    
    user_id = request.session.get('user_id')
    appointments = Appointment.objects.filter(client_id=user_id).order_by('-created_at')
    
    all_notifications = Notification.objects.filter(user_id=user_id).order_by('-sent_at')
    unread_count = Notification.objects.filter(user_id=user_id, is_read=False).count()
    
    notifications_list = []
    for notif in all_notifications[:20]:
        notifications_list.append({
            'id': notif.id,
            'type': notif.notification_type.lower(),
            'title': get_notification_title(notif.notification_type),
            'message': notif.message,
            'time': format_notification_time(notif.sent_at),
        })
    
    notifications_json = json.dumps(notifications_list)
    
    context = {
        'appointments': appointments,
        'unread_count': unread_count,
        'notifications_json': notifications_json,
    }
    
    context.update(get_user_context(user_id))
    
    return render(request, 'client_app/dashboard.html', context)

def get_notification_title(notification_type):
    """Get human-readable title for notification type"""
    titles = {
        'confirmation': 'Booking Confirmed',
        'approval': 'Appointment Approved',
        'rejection': 'Appointment Rejected',
        'reminder': 'Appointment Reminder',
        'cancellation': 'Appointment Cancelled',
        'edited': 'Appointment Modified',
    }
    return titles.get(notification_type.lower(), 'Notification')

def format_notification_time(sent_at):
    """Format notification time in readable format"""
    if not sent_at:
        return 'Just now'
    
    from django.utils import timezone
    now = timezone.now()
    diff = now - sent_at
    
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = seconds // 60
        return f'{minutes}m ago'
    elif seconds < 86400:
        hours = seconds // 3600
        return f'{hours}h ago'
    else:
        days = seconds // 86400
        return f'{days}d ago'

def book_appointment(request):
    """Book appointment - show available dates and time slots"""
    if request.session.get('user_role') != 'client':
        return redirect('client_login')
    
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        service_id = request.POST.get('service_id')
        staff_id = request.POST.get('staff_id')
        appointment_date_str = request.POST.get('appointment_date')
        appointment_time_str = request.POST.get('appointment_time')
        
        try:
            if not all([service_id, staff_id, appointment_date_str, appointment_time_str]):
                messages.error(request, "Please fill in all required fields!")
                return redirect('client_book')
            
            service = Service.objects.get(id=service_id)
            staff = CustomUser.objects.get(id=staff_id, role='staff')
            
            if not service.staff.filter(id=staff_id).exists():
                messages.error(request, "This staff member doesn't provide this service!")
                return redirect('client_book')
            
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            existing_booking = Appointment.objects.filter(
                service=service,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'approved', 'serving']
            ).first()
            
            if existing_booking:
                messages.error(request, "This time slot has already been booked. Please choose another time.")
                return redirect('client_book')
            
            availability = StaffAvailability.objects.filter(
                staff=staff,
                date=appointment_date,
                start_time=appointment_time,
                is_available=True
            ).first()
            
            if not availability:
                messages.error(request, "Selected time slot is no longer available!")
                return redirect('client_book')
            
            appointment = Appointment.objects.create(
                client_id=user_id,
                service=service,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='pending'
            )

            notify_appointment_booked(appointment)

            messages.success(request, f"Appointment booked for {appointment_date} at {appointment_time_str}! Waiting for staff approval.")
            return redirect('client_dashboard')
        
        except Service.DoesNotExist:
            messages.error(request, "Service not found!")
        except CustomUser.DoesNotExist:
            messages.error(request, "Staff member not found!")
        except ValueError:
            messages.error(request, "Invalid date or time format!")
        except Exception as e:
            messages.error(request, f"Error booking appointment: {str(e)}")
        
        return redirect('client_book')
    
    services = Service.objects.filter(staff__isnull=False).distinct()
    
    staff_by_service = {}
    available_dates_by_staff = {}
    time_slots_by_staff_date = {}
    
    today = datetime.now().date()
    
    for service in services:
        staff_list = service.staff.filter(role='staff')
        staff_by_service[service.id] = [
            {'id': s.id, 'name': f"{s.first_name} {s.last_name}"} 
            for s in staff_list
        ]
        
        for staff in staff_list:
            available = StaffAvailability.objects.filter(
                staff=staff,
                is_available=True,
                date__gte=today
            ).order_by('date', 'start_time')
            
            booked_appointments = Appointment.objects.filter(
                service__staff=staff,
                status__in=['pending', 'approved', 'serving']
            ).values_list('appointment_date', 'appointment_time')
            
            booked_set = set()
            for booked_date, booked_time in booked_appointments:
                booked_set.add((booked_date.isoformat(), booked_time.strftime('%H:%M')))
            
            dates_set = set()
            for av in available:
                date_iso = av.date.isoformat()
                time_str = av.start_time.strftime('%H:%M')
                
                if (date_iso, time_str) not in booked_set:
                    dates_set.add(date_iso)
            
            dates_list = sorted(list(dates_set))
            available_dates_by_staff[staff.id] = json.dumps(dates_list)
            
            slots_by_date = {}
            for av in available:
                date_key = av.date.isoformat()
                time_str = av.start_time.strftime('%H:%M')
                
                if (date_key, time_str) in booked_set:
                    continue
                
                if date_key not in slots_by_date:
                    slots_by_date[date_key] = []
                
                time_slot = {
                    'start_time': time_str,
                    'end_time': av.end_time.strftime('%H:%M'),
                }
                slots_by_date[date_key].append(time_slot)
            
            for date_key, slots in slots_by_date.items():
                key = f"{staff.id}_{date_key}"
                time_slots_by_staff_date[key] = json.dumps(slots)
    
    context = {
        'services': services,
        'staff_by_service': json.dumps(staff_by_service),
        'available_dates_by_staff': available_dates_by_staff,
        'time_slots_by_staff_date': time_slots_by_staff_date,
    }
    
    return render(request, 'client_app/book.html', context)

def edit_appointment(request, appointment_id):
    """Edit a pending or rejected appointment"""
    if request.session.get('user_role') != 'client':
        return redirect('client_login')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id, client_id=request.session.get('user_id'))
        
        if appointment.status not in ['pending', 'rejected']:
            messages.error(request, "You can only edit pending or rejected appointments")
            return redirect('client_dashboard')
        
        if request.method == 'POST':
            service_id = request.POST.get('service_id')
            staff_id = request.POST.get('staff_id')
            appointment_date_str = request.POST.get('appointment_date')
            appointment_time_str = request.POST.get('appointment_time')
            
            try:
                service = Service.objects.get(id=service_id)
                staff = CustomUser.objects.get(id=staff_id, role='staff')
                
                if not service.staff.filter(id=staff_id).exists():
                    messages.error(request, "This staff member doesn't provide this service!")
                    return redirect('edit_appointment', appointment_id=appointment_id)
                
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
                
                existing_booking = Appointment.objects.filter(
                    service=service,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status__in=['pending', 'approved', 'serving']
                ).exclude(id=appointment.id).first()
                
                if existing_booking:
                    messages.error(request, "This time slot is already booked. Please choose another.")
                    return redirect('edit_appointment', appointment_id=appointment_id)
                
                availability = StaffAvailability.objects.filter(
                    staff=staff,
                    date=appointment_date,
                    start_time=appointment_time,
                    is_available=True
                ).first()
                
                if not availability:
                    messages.error(request, "This date/time is no longer available!")
                    return redirect('edit_appointment', appointment_id=appointment_id)
                
                # Store old details for notification
                old_date = appointment.appointment_date
                old_time = appointment.appointment_time
                
                # Update appointment
                appointment.service = service
                appointment.appointment_date = appointment_date
                appointment.appointment_time = appointment_time
                appointment.status = 'pending'
                appointment.queue_number = None
                appointment.save()
                
                # Send notification to staff that appointment was edited
                notify_appointment_edited(appointment, old_date, old_time)
                
                messages.success(request, "Appointment updated successfully! Staff has been notified of the change.")
                return redirect('client_dashboard')
            
            except ValueError:
                messages.error(request, "Invalid date or time format!")
            except Exception as e:
                messages.error(request, f"Error updating appointment: {str(e)}")
            
            return redirect('edit_appointment', appointment_id=appointment_id)
        
        services = Service.objects.filter(staff__isnull=False).distinct()
        
        staff_by_service = {}
        available_dates_by_staff = {}
        time_slots_by_staff_date = {}
        
        today = datetime.now().date()
        
        for service in services:
            staff_list = service.staff.filter(role='staff')
            staff_by_service[service.id] = [
                {'id': s.id, 'name': f"{s.first_name} {s.last_name}"} 
                for s in staff_list
            ]
            
            for staff in staff_list:
                available = StaffAvailability.objects.filter(
                    staff=staff,
                    is_available=True,
                    date__gte=today
                ).order_by('date', 'start_time')
                
                booked_appointments = Appointment.objects.filter(
                    service__staff=staff,
                    status__in=['pending', 'approved', 'serving']
                ).exclude(id=appointment.id).values_list('appointment_date', 'appointment_time')
                
                booked_set = set()
                for booked_date, booked_time in booked_appointments:
                    booked_set.add((booked_date.isoformat(), booked_time.strftime('%H:%M')))
                
                dates_set = set()
                for av in available:
                    date_iso = av.date.isoformat()
                    time_str = av.start_time.strftime('%H:%M')
                    
                    if (date_iso, time_str) not in booked_set:
                        dates_set.add(date_iso)
                
                dates_list = sorted(list(dates_set))
                available_dates_by_staff[staff.id] = json.dumps(dates_list)
                
                slots_by_date = {}
                for av in available:
                    date_key = av.date.isoformat()
                    time_str = av.start_time.strftime('%H:%M')
                    
                    if (date_key, time_str) in booked_set:
                        continue
                    
                    if date_key not in slots_by_date:
                        slots_by_date[date_key] = []
                    
                    time_slot = {
                        'start_time': time_str,
                        'end_time': av.end_time.strftime('%H:%M'),
                    }
                    slots_by_date[date_key].append(time_slot)
                
                for date_key, slots in slots_by_date.items():
                    key = f"{staff.id}_{date_key}"
                    time_slots_by_staff_date[key] = json.dumps(slots)
        
        context = {
            'appointment': appointment,
            'services': services,
            'staff_by_service': json.dumps(staff_by_service),
            'available_dates_by_staff': available_dates_by_staff,
            'time_slots_by_staff_date': time_slots_by_staff_date,
        }
        
        return render(request, 'client_app/edit_appointment.html', context)
    
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found!")
        return redirect('client_dashboard')

def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    print("\n" + "="*50)
    print("🔵 CANCEL_APPOINTMENT FUNCTION CALLED")
    print("="*50)
    
    if request.session.get('user_role') != 'client':
        print("❌ Not a client, redirecting to login")
        return redirect('client_login')
    
    user_id = request.session.get('user_id')
    print(f"Client ID: {user_id}")
    print(f"Appointment ID: {appointment_id}")
    
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, 
            client_id=user_id
        )
        print(f"✅ Found appointment: {appointment.service.name}")
        
        if appointment.status == 'completed':
            print("❌ Appointment already completed, can't cancel")
            messages.error(request, "Cannot cancel completed appointments")
            return redirect('client_dashboard')
        
        appointment_date = appointment.appointment_date
        appointment_time = appointment.appointment_time.strftime('%H:%M')
        
        print(f"Service: {appointment.service.name}")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")
        
        # Get staff members who provide this service
        staff_members = appointment.service.staff.filter(role='staff')
        print(f"✅ Found {staff_members.count()} staff members for this service")
        
        # Create notifications for each staff member
        client_name = f"{appointment.client.first_name} {appointment.client.last_name}"
        notification_message = f"Appointment cancelled by {client_name} for {appointment.service.name} on {appointment_date.strftime('%B %d, %Y')} at {appointment_time}. The time slot is now available."
        
        print(f"Creating notifications...")
        for staff in staff_members:
            print(f"  - Creating notification for staff: {staff.first_name} {staff.last_name}")
            
            notif = Notification.objects.create(
                user=staff,
                appointment=appointment,
                message=notification_message,
                notification_type='cancellation'
            )
            print(f"    ✅ Notification created! ID: {notif.id}")
        
        # Delete the appointment
        print(f"Deleting appointment...")
        appointment.delete()
        print(f"✅ Appointment deleted!")
        
        messages.success(request, f"Appointment on {appointment_date} at {appointment_time} has been cancelled. Staff has been notified.")
        print("🟢 CANCEL_APPOINTMENT COMPLETE - SUCCESS")
        
    except Appointment.DoesNotExist:
        print(f"❌ Appointment not found for user {user_id} with ID {appointment_id}")
        messages.error(request, "Appointment not found!")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error: {str(e)}")
    
    print("="*50 + "\n")
    return redirect('client_dashboard')

def client_analytics_view(request):
    """Display analytics dashboard for client"""
    if request.session.get('user_role') != 'client':
        return redirect('client_login')
    
    client_id = request.session.get('user_id')
    
    total = Appointment.objects.filter(client_id=client_id).count()
    completed = Appointment.objects.filter(client_id=client_id, status='completed').count()
    upcoming = Appointment.objects.filter(
        client_id=client_id,
        status__in=['pending', 'approved'],
        appointment_date__gte=date.today()
    ).count()
    rejected = Appointment.objects.filter(client_id=client_id, status='rejected').count()
    
    most_booked = Appointment.objects.filter(
        client_id=client_id,
        status='completed'
    ).values('service__name').annotate(count=Count('id')).order_by('-count').first()
    
    analytics = {
        'total_appointments': total,
        'completed_appointments': completed,
        'upcoming_appointments': upcoming,
        'rejected_appointments': rejected,
        'most_booked_service': most_booked['service__name'] if most_booked else 'N/A',
    }
    
    upcoming_apps = Appointment.objects.filter(
        client_id=client_id,
        status__in=['pending', 'approved'],
        appointment_date__gte=date.today()
    ).order_by('appointment_date').select_related('service')[:5]
    
    context = {
        'analytics': analytics,
        'upcoming_appointments': upcoming_apps,
    }
    
    context.update(get_user_context(client_id))
    
    return render(request, 'client_app/analytics.html', context)