# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .forms import ClientRegistrationForm, VerifyAccountForm, LoginForm, EmployeeForm
from .models import CustomUser, ClientProfile, EmployeeProfile
from .decorators import employee_required, client_required


def client_register_view(request):
    if request.user.is_authenticated:
         return redirect('client_dashboard')

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                email = form.cleaned_data['email']
                fname = form.cleaned_data['first_name']
                lname = form.cleaned_data['last_name']
                password = form.cleaned_data['password1']

                user = CustomUser.objects.create_user(
                    email=email,
                    first_name=fname,
                    last_name=lname,
                    password=password,
                    phone_number=form.cleaned_data.get('phone_number'),
                    is_employee=False,
                    is_verified=False
                )
                user.generate_verification_code()

                ClientProfile.objects.create(
                    user=user,
                    organization=form.cleaned_data.get('organization'),
                    address=form.cleaned_data.get('address'),
                    city=form.cleaned_data.get('city'),
                    country=form.cleaned_data.get('country'),
                    date_of_birth=form.cleaned_data.get('date_of_birth'),
                    gender=form.cleaned_data.get('gender'),
                )

                user.send_verification_email()
                login(request, user)
                messages.info(request, "Registration successful! Please check your email for a verification code.")
                return redirect('verify_account')
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = ClientRegistrationForm()

    return render(request, 'users/register_client.html', {'form': form})


@login_required
def verify_account_view(request):
    user = request.user
    if user.is_verified:
        return redirect('client_dashboard' if not user.is_employee else 'employee_dashboard')

    if request.method == 'POST':
        form = VerifyAccountForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            if user.verification_code == code and \
               user.verification_code_expires and \
               user.verification_code_expires > timezone.now():

                user.is_verified = True
                user.verification_code = None
                user.verification_code_expires = None
                user.save(update_fields=['is_verified', 'verification_code', 'verification_code_expires'])
                messages.success(request, "Account verified successfully!")
                return redirect('client_dashboard' if not user.is_employee else 'employee_dashboard')
            else:
                messages.error(request, 'Invalid or expired verification code.')
    else:
        form = VerifyAccountForm()

    return render(request, 'users/verify_account.html', {'form': form})


def user_login_view(request):
    if request.user.is_authenticated:
         return redirect('client_dashboard' if not request.user.is_employee else 'employee_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if user.is_verified:
                    messages.success(request, f"Welcome back, {user.full_name}!")
                    return redirect('client_dashboard' if not user.is_employee else 'employee_dashboard')
                else:
                    messages.info(request, "Please verify your account.")
                    return redirect('verify_account')
            else:
                messages.error(request, "Invalid email or password.")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def user_logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('user_login')


@employee_required
def manage_employees_view(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.create_employee(
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password'] # Pass the password from form
                )
                EmployeeProfile.objects.create(
                    user=user,
                    job_title=form.cleaned_data.get('job_title'),
                    department=form.cleaned_data.get('department'),
                    gender=form.cleaned_data.get('gender')
                )
                messages.success(request, "Employee added successfully.")
                # Consider sending login details via email here
                return redirect('manage_employees')
            except Exception as e:
                messages.error(request, f"Failed to add employee: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    employees = EmployeeProfile.objects.select_related('user').all()
    context = {
        'form': form,
        'employees': employees,
    }
    return render(request, 'users/manage_employees.html', context)