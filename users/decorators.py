from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps

def client_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('user_login') # Redirect to your login URL name
        if request.user.is_employee:
            messages.error(request, "This page is only accessible to clients.")
            # Redirect employees away, maybe to their dashboard
            return redirect('employee_dashboard') # Or appropriate employee URL
        if not request.user.is_verified:
             messages.warning(request, "Please verify your account first.")
             return redirect('verify_account') # Redirect to verification page
        return function(request, *args, **kwargs)
    return wrap

def employee_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('user_login')
        if not request.user.is_employee:
            messages.error(request, "This page is only accessible to employees.")
            # Redirect non-employees away, maybe to client dashboard
            return redirect('client_dashboard') # Or appropriate client URL
        # Employees added by admin are assumed verified, but check just in case
        if not request.user.is_verified:
             messages.warning(request, "Please verify your account first.")
             return redirect('verify_account')
        # Optionally check for is_staff as well if admin functions require it
        # if not request.user.is_staff:
        #     messages.error(request, "Admin privileges required.")
        #     return redirect('client_dashboard') # Or a permission denied page
        return function(request, *args, **kwargs)
    return wrap

# Optional: Decorator to ensure user is verified, regardless of role
def verification_required(function):
     @wraps(function)
     def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in.")
            return redirect('user_login')
        if not request.user.is_verified:
             messages.warning(request, "Please verify your account first.")
             return redirect('verify_account')
        return function(request, *args, **kwargs)
     return wrap