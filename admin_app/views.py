from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from appointments.models import CustomUser, Service, Appointment, StaffAvailability, Notification
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from datetime import date

import secrets
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password

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
            'user_first_name': 'Admin',
            'user_last_name': '',
        }
        
def admin_register(request):
    """Simple admin registration - restrict with a master password"""
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        admin_key = request.POST.get('admin_key')
        
        # ✅ SIMPLE: Just check a master key
        if admin_key != os.getenv('ADMIN_KEY'):  
            messages.error(request, "❌ Invalid admin key!")
            return redirect('admin_register')
        
        if password != password_confirm:
            messages.error(request, "❌ Passwords don't match!")
            return redirect('admin_register')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "❌ Email already exists!")
            return redirect('admin_register')
        
        if len(password) < 6:
            messages.error(request, "❌ Password must be at least 6 characters!")
            return redirect('admin_register')
        
        CustomUser.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            role='admin'
        )
        messages.success(request, "✅ Admin account created! Now login.")
        return redirect('admin_login')
    
    return render(request, 'admin_app/register.html')

def admin_login(request):
    """Admin login view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        print(f"\n{'='*60}")
        print(f"ADMIN LOGIN ATTEMPT")
        print(f"Email: {email}")
        print(f"{'='*60}\n")
        
        try:
            user = CustomUser.objects.get(email=email, role='admin')
            print(f"✅ Admin found: {user.first_name} {user.last_name}")
            
            if check_password(password, user.password):
                print(f"✅ Password correct!")
                
                # ✅ SET SESSION VARIABLES
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = 'admin'
                request.session['admin_name'] = f"{user.first_name} {user.last_name}"
                
                print(f"✅ Session set successfully")
                print(f"   - user_id: {user.id}")
                print(f"   - user_role: admin")
                print(f"   - admin_name: {user.first_name} {user.last_name}")
                print(f"{'='*60}\n")
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('admin_dashboard')
            else:
                print(f"❌ Password incorrect!")
                messages.error(request, "Admin not found!")
                return redirect('admin_login')
        
        except CustomUser.DoesNotExist:
            print(f"❌ No admin found with email: {email}")
            messages.error(request, "Admin not found!")
            return redirect('admin_login')
    
    return render(request, 'admin_app/login.html')

def forgot_password(request):
    """Admin forgot password view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please enter your email!')
            return redirect('admin_forgot_password')
        
        try:
            admin = CustomUser.objects.get(email=email, role='admin')
            
            # Generate temporary password
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            
            # Update admin password
            admin.password = make_password(temp_password)
            admin.save()
            
            # Send email with temporary password
            try:
                send_mail(
                    subject='QueueSmart - Password Reset',
                    message=f"""
Hello {admin.first_name},

You requested a password reset for your admin account.

Your temporary password is: {temp_password}

Please log in with this password and change it to something more secure.

Best regards,
QueueSmart Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, f'Password reset email sent to {email}. Check your inbox!')
            except Exception as e:
                messages.warning(request, f'Password reset but email failed to send: {str(e)}')
            
            return redirect('admin_login')
        
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.success(request, 'If an admin account exists with that email, a reset link will be sent.')
            return redirect('admin_login')
    
    return render(request, 'admin_app/forgot_password.html')


def admin_dashboard(request):
    """Admin dashboard"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    admin_id = request.session.get('user_id')
    
    try:
        admin = CustomUser.objects.get(id=admin_id, role='admin')
    except CustomUser.DoesNotExist:
        return redirect('admin_login')
    
    # Get all staff, services, clients
    staff_members = CustomUser.objects.filter(role='staff').order_by('-date_joined')
    services = Service.objects.all().order_by('name')
    all_clients = CustomUser.objects.filter(role='client').order_by('-date_joined')
    
    total_appointments = Appointment.objects.count()
    total_clients = all_clients.count()
    
    context = {
        'staff_members': staff_members,
        'services': services,
        'all_clients': all_clients,
        'total_appointments': total_appointments,
        'total_clients': total_clients,
        'user_first_name': admin.first_name,  # ✅ ADD THIS
    }
    
    return render(request, 'admin_app/dashboard.html', context)

def create_staff(request):
    """Admin creates a new staff member and assigns services"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        service_ids = request.POST.getlist('services')  # ✅ GET SELECTED SERVICES
        
        # Validate inputs
        if not all([email, first_name, last_name, password, service_ids]):
            messages.error(request, "All fields including at least one service are required!")
            return redirect('admin_create_staff')
        
        if password != password_confirm:
            messages.error(request, "Passwords don't match!")
            return redirect('admin_create_staff')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('admin_create_staff')
        
        # Create staff member
        staff = CustomUser.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            password=make_password(password),
            role='staff'
        )
        
        # ✅ ASSIGN SERVICES TO STAFF
        services = Service.objects.filter(id__in=service_ids)
        for service in services:
            service.staff.add(staff)
        
        messages.success(request, f"Staff member {first_name} {last_name} created with {services.count()} services!")
        return redirect('admin_dashboard')
    
    # GET request - show form
    services = Service.objects.all()
    
    context = {
        'services': services,
    }
    
    context.update(get_user_context(request.session.get('user_id')))
    
    return render(request, 'admin_app/create_staff.html', context)

def logout(request):
    request.session.flush()
    return redirect('admin_login')

def edit_staff(request, staff_id):
    """Admin edits a staff member's details and services"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    try:
        staff = CustomUser.objects.get(id=staff_id, role='staff')
    except CustomUser.DoesNotExist:
        messages.error(request, "Staff member not found!")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        service_ids = request.POST.getlist('services')  # ✅ GET SELECTED SERVICES
        
        # Validate inputs
        if not all([first_name, last_name, service_ids]):
            messages.error(request, "All fields including at least one service are required!")
            return redirect(f'/admin/edit-staff/{staff_id}/')
        
        # Update staff details
        staff.first_name = first_name
        staff.last_name = last_name
        staff.phone_number = phone
        staff.save()
        
        # ✅ UPDATE SERVICES - Remove old services and add new ones
        staff_services = Service.objects.filter(staff=staff)
        for service in staff_services:
            service.staff.remove(staff)
        
        # Add selected services
        services = Service.objects.filter(id__in=service_ids)
        for service in services:
            service.staff.add(staff)
        
        messages.success(request, f"Staff member {first_name} {last_name} updated successfully with {services.count()} services!")
        return redirect('admin_dashboard')
    
    # GET request - show form with current data
    services = Service.objects.all()
    staff_services = staff.services.all()  # Services this staff provides
    staff_service_ids = [str(s.id) for s in staff_services]
    
    context = {
        'staff': staff,
        'services': services,
        'staff_service_ids': staff_service_ids,
    }
    
    context.update(get_user_context(request.session.get('user_id')))
    
    return render(request, 'admin_app/edit_staff.html', context)

def reset_staff_password(request, staff_id):
    """Admin resets a staff member's password"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    try:
        staff = CustomUser.objects.get(id=staff_id, role='staff')
    except CustomUser.DoesNotExist:
        messages.error(request, "Staff member not found!")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        # Generate a new temporary password
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        
        # Update staff password
        staff.password = make_password(temp_password)
        staff.save()
        
        # Send email to staff with new password
        try:
            send_mail(
                subject='QueueSmart - Password Reset by Admin',
                message=f"""
Hello {staff.first_name},

Your password has been reset by the administrator.

Your new temporary password is: {temp_password}

Please log in with this password and change it to something more secure.

Best regards,
QueueSmart Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff.email],
                fail_silently=False,
            )
        except:
            pass  # Email failed but password is still reset
        
        messages.success(request, f"Password reset for {staff.first_name} {staff.last_name}. Email sent to {staff.email}")
        return redirect('admin_dashboard')
    
    context = {'staff': staff}
    context.update(get_user_context(request.session.get('user_id')))
    
    return render(request, 'admin_app/reset_staff_password.html', context)

def delete_staff(request, staff_id):
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    try:
        staff = CustomUser.objects.get(id=staff_id, role='staff')
        staff.delete()
        messages.success(request, f"Staff member deleted successfully!")
    except CustomUser.DoesNotExist:
        messages.error(request, "Staff member not found!")
    
    return redirect('admin_dashboard')


def delete_user(request, user_id):
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Prevent deleting admin accounts
        if user.role == 'admin':
            messages.error(request, "Cannot delete admin accounts!")
            return redirect('admin_dashboard')
        
        username = f"{user.first_name} {user.last_name}"
        user.delete()
        messages.success(request, f"{username} has been deleted!")
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found!")
    
    return redirect('admin_dashboard')


def create_service(request):
    """Admin creates a new service"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        duration = request.POST.get('duration')
        
        # Validate inputs
        if not all([name, description, duration]):
            messages.error(request, "All fields are required!")
            return redirect('admin_create_service')
        
        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError("Duration must be positive")
        except ValueError:
            messages.error(request, "Duration must be a valid positive number (in minutes)!")
            return redirect('admin_create_service')
        
        # Check if service already exists
        if Service.objects.filter(name=name).exists():
            messages.error(request, "A service with this name already exists!")
            return redirect('admin_create_service')
        
        # Create service
        Service.objects.create(
            name=name,
            description=description,
            duration=duration
        )
        
        messages.success(request, f"Service '{name}' created successfully!")
        return redirect('admin_dashboard')
    
    # GET request - show form
    context = {}
    context.update(get_user_context(request.session.get('user_id')))
    
    return render(request, 'admin_app/create_service.html', context)


def edit_service(request, service_id):
    """Edit an existing service"""
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        messages.error(request, 'Service not found!')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        duration = request.POST.get('duration')
        staff_ids = request.POST.getlist('staff')
        
        # Validation
        if not name or not description or not duration:
            messages.error(request, 'Please fill in all fields!')
            return redirect('admin_edit_service', service_id=service_id)
        
        try:
            duration = int(duration)
            if duration <= 0:
                messages.error(request, 'Duration must be a positive number!')
                return redirect('admin_edit_service', service_id=service_id)
        except ValueError:
            messages.error(request, 'Duration must be a number!')
            return redirect('admin_edit_service', service_id=service_id)
        
        if not staff_ids:
            messages.error(request, 'Please assign at least one staff member!')
            return redirect('admin_edit_service', service_id=service_id)
        
        # Update service
        service.name = name
        service.description = description
        service.duration = duration
        service.save()
        
        # Update staff assignments
        service.staff.clear()
        for staff_id in staff_ids:
            try:
                staff = CustomUser.objects.get(id=staff_id, role='staff')
                service.staff.add(staff)
            except CustomUser.DoesNotExist:
                pass
        
        messages.success(request, f'Service "{name}" updated successfully!')
        return redirect('admin_dashboard')
    
    # GET request - show edit form
    all_staff = CustomUser.objects.filter(role='staff')
    context = {
        'service': service,
        'all_staff': all_staff,
        'admin_name': request.session.get('admin_name', 'Admin')
    }
    return render(request, 'admin_app/edit_service.html', context)


def delete_service(request, service_id):
    """Delete a service"""
    try:
        service = Service.objects.get(id=service_id)
        service_name = service.name
        service.delete()
        messages.success(request, f'Service "{service_name}" deleted successfully!')
    except Service.DoesNotExist:
        messages.error(request, 'Service not found!')
    
    return redirect('admin_dashboard')

# ===== ANALYTICS FUNCTIONS =====

def get_system_analytics():
    """Get overall system analytics (for admin)"""
    
    total_appointments = Appointment.objects.count()
    total_clients = CustomUser.objects.filter(role='client').count()
    total_staff = CustomUser.objects.filter(role='staff').count()
    total_services = Service.objects.count()
    
    # Appointments by status
    status_breakdown = Appointment.objects.values('status').annotate(count=Count('id'))
    
    # Busiest services
    busiest_services = Appointment.objects.values('service__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Busiest staff
    busiest_staff = Appointment.objects.values('service__staff__first_name', 'service__staff__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Today's stats
    today = date.today()
    todays_appointments = Appointment.objects.filter(appointment_date=today).count()
    todays_completed = Appointment.objects.filter(
        appointment_date=today,
        status='completed'
    ).count()
    
    return {
        'total_appointments': total_appointments,
        'total_clients': total_clients,
        'total_staff': total_staff,
        'total_services': total_services,
        'status_breakdown': list(status_breakdown),
        'busiest_services': list(busiest_services),
        'busiest_staff': list(busiest_staff),
        'todays_appointments': todays_appointments,
        'todays_completed': todays_completed,
    }

def admin_analytics_view(request):
    """Display analytics dashboard for admin"""
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    analytics = get_system_analytics()
    
    context = {
        'analytics': analytics,
    }
    
    return render(request, 'admin_app/analytics.html', context)

