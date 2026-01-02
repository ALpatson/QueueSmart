from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from appointments.models import CustomUser, Appointment, StaffAvailability, Service, Notification
from datetime import datetime, timedelta
import datetime as dt
import json
from django.db.models import Count
from datetime import date

from notifications.views import (
    notify_appointment_approved,
    notify_appointment_rejected,
    notify_appointment_serving,
    notify_appointment_completed
)

def staff_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = CustomUser.objects.get(email=email, role='staff')
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = 'staff'
                return redirect('staff_dashboard')
            else:
                messages.error(request, "Invalid password!")
        except CustomUser.DoesNotExist:
            messages.error(request, "Staff account not found!")
        
        return redirect('staff_login')
    
    return render(request, 'staff_app/login.html')

def logout(request):
    request.session.flush()
    return redirect('staff_login')

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

def staff_dashboard(request):
    """Staff dashboard"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    
    try:
        staff = CustomUser.objects.get(id=staff_id, role='staff')
    except CustomUser.DoesNotExist:
        return redirect('staff_login')
    
    # Get services for this staff
    services = staff.services.all()
    
    # Get pending appointments
    pending = Appointment.objects.filter(
        status='pending',
        service__in=services
    ).select_related('client', 'service', 'staff').order_by('-created_at')
    
    # Get approved queue
    approved = Appointment.objects.filter(
        status='approved',
        staff=staff
    ).select_related('client', 'service', 'staff').order_by('queue_number')
    
    # Get serving
    serving = Appointment.objects.filter(
        status='serving',
        staff=staff
    ).first()
    
    # Get unread count
    unread_count = Notification.objects.filter(
        user_id=staff_id,
        is_read=False
    ).count()
    
    # Get notifications
    all_notifications = Notification.objects.filter(
        user_id=staff_id
    ).order_by('-sent_at')
    
    notifications_list = []
    for notif in all_notifications:
        notifications_list.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': f"{notif.notification_type.upper()}",
            'message': notif.message,
            'time': notif.sent_at.strftime('%b %d, %Y at %I:%M %p'),
        })
    
    import json
    notifications_json = json.dumps(notifications_list)
    
    context = {
        'staff_name': f"{staff.first_name} {staff.last_name}",
        'pending': pending,
        'approved': approved,
        'serving': serving,
        'unread_count': unread_count,
        'notifications_json': notifications_json,
        'user_first_name': staff.first_name,  # ✅ ADD THIS
    }
    
    return render(request, 'staff_app/dashboard.html', context)

def change_password(request):
    """Staff member change their password"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    staff = CustomUser.objects.get(id=staff_id)
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate old password
        if not check_password(old_password, staff.password):
            messages.error(request, "❌ Current password is incorrect!")
            return redirect('staff_change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, "❌ New passwords don't match!")
            return redirect('staff_change_password')
        
        # Check password length
        if len(new_password) < 6:
            messages.error(request, "❌ New password must be at least 6 characters!")
            return redirect('staff_change_password')
        
        # Update password
        staff.password = make_password(new_password)
        staff.save()
        
        messages.success(request, "✅ Password changed successfully! Please log in again.")
        return redirect('staff_login')
    
    context = {}
    context.update(get_user_context(staff_id))
    
    return render(request, 'staff_app/change_password.html', context)

def approve_appointment(request, id):
    """Approve a pending appointment"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    
    try:
        staff = CustomUser.objects.get(id=staff_id, role='staff')
        app = Appointment.objects.get(id=id)
        
        print(f"\n{'='*60}")
        print(f"STAFF APPROVE - DEBUG")
        print(f"{'='*60}")
        print(f"Staff ID: {staff_id}")
        print(f"Staff Name: {staff.first_name} {staff.last_name}")
        print(f"Appointment ID: {id}")
        print(f"Appointment Status Before: {app.status}")
        print(f"Appointment Staff Before: {app.staff}")
        
        # Get the next queue number
        last = Appointment.objects.filter(status='approved').order_by('-queue_number').first()
        next_queue_number = (last.queue_number + 1) if last and last.queue_number else 1
        
        # ✅ IMPORTANT: Set the staff member who is approving
        app.status = 'approved'
        app.staff = staff  # ✅ THIS IS KEY - assign the staff member
        app.queue_number = next_queue_number
        app.save()
        
        print(f"Appointment Status After: {app.status}")
        print(f"Appointment Staff After: {app.staff}")
        print(f"Queue Number: {next_queue_number}")
        print(f"{'='*60}\n")
        
        # Send notification to client
        notify_appointment_approved(app)
        messages.success(request, f"Approved! Queue #{app.queue_number}")
    except CustomUser.DoesNotExist:
        messages.error(request, "Staff not found!")
    except Appointment.DoesNotExist:
        messages.error(request, "Error approving appointment")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('staff_dashboard')

def reject_appointment(request, id):
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    try:
        app = Appointment.objects.get(id=id)
        app.status = 'rejected'
        app.save()
        notify_appointment_rejected(app)
        messages.success(request, "Appointment rejected")
    except:
        messages.error(request, "Error rejecting appointment")
    
    return redirect('staff_dashboard')

def mark_serving(request, id):
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    try:
        appointment = Appointment.objects.get(id=id)
        Appointment.objects.filter(status='serving').update(status='completed')
        appointment.status = 'serving'
        appointment.save()
        notify_appointment_serving(appointment)
        messages.success(request, f"Now serving Queue #{appointment.queue_number}")
    except:
        messages.error(request, "Error")
    
    return redirect('staff_dashboard')

def complete_appointment(request, id):
    """Mark the currently serving appointment as completed"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    try:
        appointment = Appointment.objects.get(id=id, status='serving')
        queue_number = appointment.queue_number
        appointment.status = 'completed'
        appointment.save()
        notify_appointment_completed(appointment)
        messages.success(request, f"Queue #{queue_number} completed! ✓")
    except Appointment.DoesNotExist:
        messages.error(request, "This appointment is not currently being served")
    except Exception as e:
        messages.error(request, f"Error completing appointment: {str(e)}")
    
    return redirect('staff_dashboard')

def availability_calendar(request):
    """Staff member can set their available dates with multiple time slots"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get all availabilities for this month
    availabilities = StaffAvailability.objects.filter(
        staff_id=staff_id,
        date__year=year,
        date__month=month
    ).order_by('date', 'start_time')
    
    # Group by date
    dates_dict = {}
    for av in availabilities:
        date_key = av.date.isoformat()
        if date_key not in dates_dict:
            dates_dict[date_key] = []
        
        dates_dict[date_key].append({
            'id': av.id,
            'start': av.start_time.strftime('%H:%M'),
            'end': av.end_time.strftime('%H:%M'),
            'is_available': av.is_available,
        })
    
    # Generate calendar with proper structure
    from calendar import monthcalendar, month_name
    import datetime as dt
    
    days_in_month = monthcalendar(year, month)
    calendar_days = []
    
    for week in days_in_month:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0})
            else:
                date_obj = dt.date(year, month, day)
                date_str = date_obj.isoformat()
                
                # Get time slots for this date
                time_slots = dates_dict.get(date_str, [])
                
                # Determine status
                if time_slots:
                    # Check if any slot is available
                    has_available = any(slot['is_available'] for slot in time_slots)
                    has_occupied = any(not slot['is_available'] for slot in time_slots)
                    
                    if has_available and not has_occupied:
                        status = 'available'
                    elif has_occupied and not has_available:
                        status = 'occupied'
                    else:
                        status = 'mixed'
                else:
                    status = 'not-set'
                
                week_data.append({
                    'day': day,
                    'date_str': date_str,
                    'time_slots': time_slots,
                    'status': status,
                })
        calendar_days.append(week_data)
    
    # Calculate next/previous month
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    context = {
        'year': year,
        'month': month,
        'month_name': month_name[month],
        'calendar_days': calendar_days,
        'next_year': next_year,
        'next_month': next_month,
        'prev_year': prev_year,
        'prev_month': prev_month,
    }
    
    return render(request, 'staff_app/availability_calendar.html', context)

def add_time_slot(request, date_str):
    """Add a new time slot for a specific date"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    if request.method == 'POST':
        staff_id = request.session.get('user_id')
        
        try:
            # Parse the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            is_available = request.POST.get('is_available') == 'on'
            
            # Validate times
            if not start_time_str or not end_time_str:
                messages.error(request, "Start time and end time are required!")
                return redirect(f'/staff/availability/?year={date_obj.year}&month={date_obj.month}')
            
            # Parse times
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Validate time range
            if start_time >= end_time:
                messages.error(request, "Start time must be before end time!")
                return redirect(f'/staff/availability/?year={date_obj.year}&month={date_obj.month}')
            
            # Create new time slot
            StaffAvailability.objects.create(
                staff_id=staff_id,
                date=date_obj,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available
            )
            
            status_text = "Available ✅" if is_available else "Occupied ❌"
            messages.success(request, f'Time slot {start_time_str} - {end_time_str} added! ({status_text})')
            
        except ValueError as e:
            messages.error(request, f'Invalid time format. Use HH:MM format.')
            return redirect(f'/staff/availability/?year={date_obj.year}&month={date_obj.month}')
        except Exception as e:
            messages.error(request, f'Error saving time slot: {str(e)}')
            return redirect(f'/staff/availability/?year={date_obj.year}&month={date_obj.month}')
    
    # Redirect back to calendar
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    return redirect(f'/staff/availability/?year={date_obj.year}&month={date_obj.month}')

def delete_time_slot(request, slot_id):
    """Delete a specific time slot"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    
    try:
        slot = StaffAvailability.objects.get(id=slot_id, staff_id=staff_id)
        year = slot.date.year
        month = slot.date.month
        slot_time = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        slot.delete()
        messages.success(request, f'Time slot {slot_time} deleted!')
    except StaffAvailability.DoesNotExist:
        messages.error(request, 'Time slot not found!')
        return redirect('staff_availability')
    
    return redirect(f'/staff/availability/?year={year}&month={month}')

def toggle_availability(request, slot_id):
    """Toggle availability status of a time slot"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    
    try:
        slot = StaffAvailability.objects.get(id=slot_id, staff_id=staff_id)
        slot.is_available = not slot.is_available
        slot.save()
        
        year = slot.date.year
        month = slot.date.month
        status_text = "Available ✅" if slot.is_available else "Occupied ❌"
        slot_time = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        messages.success(request, f'Time slot {slot_time} marked as {status_text}!')
        
    except StaffAvailability.DoesNotExist:
        messages.error(request, 'Time slot not found!')
        return redirect('staff_availability')
    
    return redirect(f'/staff/availability/?year={year}&month={month}')

def get_staff_analytics(staff_id):
    """Get analytics for a specific staff member"""
    today = date.today()
    
    # Total appointments
    total_appointments = Appointment.objects.filter(
        service__staff__id=staff_id
    ).count()
    
    # Completed appointments
    completed_appointments = Appointment.objects.filter(
        service__staff__id=staff_id,
        status='completed'
    ).count()
    
    # Today's appointments
    todays_appointments = Appointment.objects.filter(
        service__staff__id=staff_id,
        appointment_date=today
    ).count()
    
    # Pending appointments
    pending_appointments = Appointment.objects.filter(
        service__staff__id=staff_id,
        status='pending'
    ).count()
    
    # Average queue time (hours between booking and completion)
    completed = Appointment.objects.filter(
        service__staff__id=staff_id,
        status='completed'
    )
    
    total_time = 0
    if completed.count() > 0:
        for appointment in completed:
            time_diff = appointment.updated_at - appointment.created_at
            total_time += time_diff.total_seconds() / 3600
        avg_wait_time = total_time / completed.count()
    else:
        avg_wait_time = 0
    
    return {
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'todays_appointments': todays_appointments,
        'pending_appointments': pending_appointments,
        'avg_wait_time': round(avg_wait_time, 2),
    }

def get_daily_schedule(staff_id):
    """Get staff's schedule for today"""
    today = date.today()
    
    appointments = Appointment.objects.filter(
        service__staff__id=staff_id,
        appointment_date=today
    ).order_by('appointment_time').select_related('client', 'service')
    
    # Group by status
    schedule = {
        'pending': [],
        'approved': [],
        'serving': None,
        'completed': [],
    }
    
    for appointment in appointments:
        app_data = {
            'id': appointment.id,
            'client': f"{appointment.client.first_name} {appointment.client.last_name}",
            'service': appointment.service.name,
            'time': appointment.appointment_time.strftime('%H:%M'),
            'queue_number': appointment.queue_number,
            'status': appointment.status,
        }
        
        if appointment.status == 'serving':
            schedule['serving'] = app_data
        elif appointment.status == 'completed':
            schedule['completed'].append(app_data)
        elif appointment.status == 'approved':
            schedule['approved'].append(app_data)
        else:
            schedule['pending'].append(app_data)
    
    return schedule

def staff_analytics_view(request):
    """Display analytics dashboard for staff"""
    if request.session.get('user_role') != 'staff':
        return redirect('staff_login')
    
    staff_id = request.session.get('user_id')
    
    analytics = get_staff_analytics(staff_id)
    schedule = get_daily_schedule(staff_id)
    
    # Get all notifications for staff
    all_notifications = Notification.objects.filter(user_id=staff_id).order_by('-sent_at')
    unread_count = Notification.objects.filter(user_id=staff_id, is_read=False).count()
    
    # Format notifications for JavaScript
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
        'analytics': analytics,
        'schedule': schedule,
        'today': date.today().strftime('%B %d, %Y'),
        'unread_count': unread_count,
        'notifications_json': notifications_json,
    }
    
    context.update(get_user_context(staff_id))
    
    return render(request, 'staff_app/analytics.html', context)