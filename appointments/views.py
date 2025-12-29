from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm
from .models import CustomUser
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
