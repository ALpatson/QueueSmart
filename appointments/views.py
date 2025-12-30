from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm, BookingForm
from .decorators import client_only, staff_only, admin_only
from .models import CustomUser, Appointment
from django.contrib.auth.hashers import make_password, check_password

def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Check if passwords match
            if form.cleaned_data['password'] != form.cleaned_data['password_confirm']:
                messages.error(request, "Passwords do not match!")
                return redirect('registration')
            
            # Check if user already exists
            if CustomUser.objects.filter(email=form.cleaned_data['email']).exists():
                messages.error(request, "Email already registered!")
                return redirect('registration')
            
            # Create user
            
            user = CustomUser.objects.create(
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=make_password(form.cleaned_data['password']),
                role=form.cleaned_data['role']
            )
            messages.success(request, "Registration successful! Please login.")
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'appointments/registration.html', {'form': form})

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Email not found!")
            return redirect('login')
        
        # Check if password is correct
        
        if check_password(password, user.password):
            # Password is correct - login successful
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_role'] = user.role
            messages.success(request, f"Welcome, {user.first_name}!")
            return redirect('/appointments/login/')   # We'll create this later
        else:
            messages.error(request, "Invalid password!")
            return redirect('login')
    
    return render(request, 'appointments/login.html')


@client_only
def book_appointment(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Create appointment
            appointment = Appointment.objects.create(
                client_id=request.session['user_id'],
                service=form.cleaned_data['service'],
                appointment_date=form.cleaned_data['appointment_date'],
                appointment_time=form.cleaned_data['appointment_time'],
                status='pending'
            )
            messages.success(request, "Appointment booked! Awaiting staff approval.")
            return redirect('/appointments/login/')
    else:
        form = BookingForm()
    
    return render(request, 'appointments/book_appointment.html', {'form': form})

@staff_only
def staff_dashboard(request):
    """Staff can view pending appointments"""
    pending_appointments = Appointment.objects.filter(status='pending')
    approved_appointments = Appointment.objects.filter(status='approved').order_by('queue_number')
    serving_appointment = Appointment.objects.filter(status='serving').first()
    
    context = {
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'serving_appointment': serving_appointment,
    }
    
    return render(request, 'appointments/staff_dashboard.html', context)

@staff_only
def approve_appointment(request, appointment_id):
    """Staff approves an appointment"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'approved'
        
        # Auto assign queue number
        last_queue = Appointment.objects.filter(status='approved').order_by('-queue_number').first()
        if last_queue and last_queue.queue_number:
            appointment.queue_number = last_queue.queue_number + 1
        else:
            appointment.queue_number = 1
        
        appointment.save()
        messages.success(request, f"Appointment approved! Queue #: {appointment.queue_number}")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found!")
    
    return redirect('staff_dashboard')


@staff_only
def reject_appointment(request, appointment_id):
    """Staff rejects an appointment"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'rejected'
        appointment.save()
        messages.success(request, f"Appointment rejected!")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found!")
    
    return redirect('staff_dashboard')

@staff_only
def mark_serving(request, appointment_id):
    """Mark appointment as currently being served"""
    try:
        # Mark all as not serving
        Appointment.objects.filter(status='approved').update(status='approved')
        
        # Mark this one as serving
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'serving'
        appointment.save()
        messages.success(request, f"Now serving Queue #{appointment.queue_number}")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found!")
    
    return redirect('staff_dashboard')