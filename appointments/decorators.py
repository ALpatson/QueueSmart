from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def login_required(view_func):
    """Check if user is logged in"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, "Please login first!")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_only(view_func):
    """Only admin can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, "Please login first!")
            return redirect('login')
        
        if request.session.get('user_role') != 'admin':
            messages.error(request, "Only administrators can access this!")
            return redirect('/appointments/login/')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_only(view_func):
    """Only staff and admin can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, "Please login first!")
            return redirect('login')
        
        role = request.session.get('user_role')
        if role not in ['admin', 'staff']:
            messages.error(request, "Only staff can access this!")
            return redirect('/appointments/login/')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def client_only(view_func):
    """Only clients can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, "Please login first!")
            return redirect('login')
        
        if request.session.get('user_role') != 'client':
            messages.error(request, "Only clients can access this!")
            return redirect('/appointments/login/')
        
        return view_func(request, *args, **kwargs)
    return wrapper