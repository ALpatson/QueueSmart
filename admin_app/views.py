from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from appointments.models import CustomUser, Appointment, Service
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from datetime import date
def admin_register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, "Passwords don't match!")
            return redirect('admin_register')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('admin_register')
        
        CustomUser.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            role='admin'
        )
        messages.success(request, "Admin account created! Now login.")
        return redirect('admin_login')
    
    return render(request, 'admin_app/register.html')

def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = CustomUser.objects.get(email=email, role='admin')
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = 'admin'
                return redirect('admin_dashboard')  # ← MAKE SURE THIS LINE IS CORRECT
        except CustomUser.DoesNotExist:
            messages.error(request, "Admin not found!")
        
        return redirect('admin_login')
    
    return render(request, 'admin_app/login.html')

def admin_dashboard(request):
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    all_users = CustomUser.objects.all()
    staff_users = CustomUser.objects.filter(role='staff')
    client_users = CustomUser.objects.filter(role='client')
    
    context = {
        'all_users': all_users,
        'staff_count': staff_users.count(),
        'client_count': client_users.count(),
        'staff_users': staff_users,
    }
    
    return render(request, 'admin_app/dashboard.html', context)

def create_staff(request):
    if request.session.get('user_role') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('create_staff')
        
        CustomUser.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            role='staff'
        )
        messages.success(request, f"Staff '{first_name} {last_name}' created! Email: {email}, Password: {password}")
        return redirect('admin_dashboard')
    
    return render(request, 'admin_app/create_staff.html')

def logout(request):
    request.session.flush()
    return redirect('admin_login')

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

