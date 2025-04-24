# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.utils import timezone
from django.db import transaction
from users.decorators import client_required, employee_required
from .models import Certificate, CertificationType, TrainingCourse, Schedule
from users.models import CustomUser, ClientProfile

from .forms import CertificationTypeForm, TrainingCourseForm, IssueCertificateForm, ScheduleForm, \
    UpdateScheduleStatusForm


@client_required
def client_dashboard_view(request):
    total_certificates = request.user.certificates.count()
    active_schedules_count = Schedule.objects.filter(
        client=request.user,
        status__in=['REQUESTED', 'SCHEDULED']
    ).count()
    recent_certificates = request.user.certificates.all()[:5]

    context = {
        'total_certificates': total_certificates,
        'active_schedules_count': active_schedules_count,  # Pass the count
        'recent_certificates': recent_certificates,
    }
    return render(request, 'core/client_dashboard.html', context)


@client_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(client=request.user).select_related('certification_type').order_by(
        '-issue_date')
    context = {
        'certificates': certificates
    }
    return render(request, 'core/my_certificates.html', context)


@client_required
def available_courses_view(request):
    courses = TrainingCourse.objects.filter(is_active=True).select_related('certification_type').order_by('start_date',
                                                                                                          'name')
    context = {
        'courses': courses
    }
    return render(request, 'core/available_courses.html', context)


@client_required
def course_detail_view(request, course_id):
    course = get_object_or_404(TrainingCourse, pk=course_id, is_active=True)
    existing_schedule = Schedule.objects.filter(client=request.user, course=course).exclude(
        status__icontains='CANCELLED').first()
    schedule_form = ScheduleForm()

    if request.method == 'POST':
        if 'cancel_schedule' in request.POST and existing_schedule:
            if existing_schedule.status in ['REQUESTED', 'SCHEDULED']:
                existing_schedule.status = 'CANCELLED_BY_USER'
                existing_schedule.save(update_fields=['status', 'updated_at'])
                messages.info(request, f"Your schedule request for {course.name} has been cancelled.")
            else:
                messages.warning(request, "This schedule cannot be cancelled.")
            return redirect('course_detail', course_id=course.id)
        # Handle scheduling form submission
        else:
            schedule_form = ScheduleForm(request.POST)
            if schedule_form.is_valid():
                if existing_schedule:
                    messages.warning(request, f"You already have an active schedule for {course.name}.")
                else:
                    event_dt = schedule_form.cleaned_data['event_datetime']
                    notes = schedule_form.cleaned_data.get('notes')

                    if event_dt < timezone.now():
                        schedule_form.add_error('event_datetime', "Selected date and time must be in the future.")
                        # Re-render with error by falling through
                    else:
                        Schedule.objects.create(
                            client=request.user,
                            course=course,
                            event_datetime=event_dt,
                            notes=notes,
                            status='REQUESTED'
                        )
                        messages.success(request,
                                         f"Your request to schedule for {course.name} on {event_dt.strftime('%Y-%m-%d %H:%M')} has been submitted.")
                        return redirect('course_detail', course_id=course.id)
            else:
                messages.success(request,
                                 f"{schedule_form.errors}")

    context = {
        'course': course,
        'existing_schedule': existing_schedule,
        'schedule_form': schedule_form,  # Pass form to template always
    }
    return render(request, 'core/course_detail.html', context)


def verify_certificate_view(request, certificate_id):
    try:
        certificate = Certificate.objects.select_related(
            'client', 'certification_type'
        ).get(id=certificate_id)
    except (Certificate.DoesNotExist, ValueError):
        return render(request, 'core/verify_certificate_not_found.html', status=404)

    context = {
        'certificate': certificate,
        'is_valid': not certificate.is_expired()
    }
    return render(request, 'core/verify_certificate.html', context)


@employee_required
def employee_dashboard_view(request):
    total_clients = CustomUser.objects.filter(is_employee=False).count()
    total_certificates_issued = Certificate.objects.count()
    active_courses = TrainingCourse.objects.filter(is_active=True).count()
    context = {
        'total_clients': total_clients,
        'total_certificates_issued': total_certificates_issued,
        'active_courses': active_courses,
    }
    return render(request, 'core/employee_dashboard.html', context)


@employee_required
def manage_certification_types_view(request):
    if request.method == 'POST':
        form = CertificationTypeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Certification Type saved successfully.")
            return redirect('manage_certification_types')
        else:
            messages.error(request, f"Please correct the errors below. {form.errors}")
    else:
        form = CertificationTypeForm()

    types = CertificationType.objects.all().order_by('name')
    context = {
        'form': form,
        'certification_types': types,
    }
    return render(request, 'core/manage_certification_types.html', context)


@employee_required
def edit_certification_type_view(request, certification_type_id):
    cert_type = get_object_or_404(CertificationType, pk=certification_type_id)
    if request.method == 'POST':
        form = CertificationTypeForm(request.POST, request.FILES, instance=cert_type)
        if form.is_valid():
            form.save()
            messages.success(request, f"Certification Type '{cert_type.name}' updated successfully.")
            return redirect('manage_certification_types')
        else:
            messages.error(request, f"Please correct the errors below. {form.errors}")
    else:
        form = CertificationTypeForm(instance=cert_type)

    context = {
        'form': form,
        'cert_type': cert_type,
    }
    return render(request, 'core/edit_certification_type.html', context)

@employee_required
def manage_courses_view(request):
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Training Course saved successfully.")
            return redirect('manage_courses')
        else:
            messages.error(request, f"Please correct the errors below. {form.errors}")
    else:
        form = TrainingCourseForm()

    courses = TrainingCourse.objects.select_related('certification_type').all().order_by('name')
    context = {
        'form': form,
        'courses': courses,
    }
    return render(request, 'core/manage_courses.html', context)


@employee_required
@transaction.atomic
def issue_certificate_view(request):
    if request.method == 'POST':
        form = IssueCertificateForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data['client']
            certification_type = form.cleaned_data['certification_type']

            if Certificate.objects.filter(client=client, certification_type=certification_type).exists():
                messages.warning(request,
                                 f"{client.full_name} already has the certificate '{certification_type.name}'.")
            else:
                try:
                    certificate = Certificate(
                        client=client,
                        certification_type=certification_type,
                        issue_date=form.cleaned_data.get('issue_date') or timezone.now().date()
                    )
                    certificate.save()  # Save once to get ID for QR code URL

                    # Trigger email sending utility here
                    # send_certificate_email(certificate) # Ensure this exists and works

                    messages.success(request,
                                     f"Certificate '{certification_type.name}' issued successfully to {client.full_name}.")
                    return redirect('issue_certificate')  # Redirect on success
                except Exception as e:
                    messages.error(request, f"Failed to issue certificate: {e}")
                    # Don't redirect, let form re-render with error
        else:
            messages.error(request, "Please correct the errors below.")
            # Don't redirect, let form re-render with errors
    else:
        form = IssueCertificateForm()

    context = {
        'form': form,
    }
    return render(request, 'core/issue_certificate.html', context)


@client_required
def my_schedule_view(request):
    schedules = Schedule.objects.filter(client=request.user).select_related('course').order_by('-event_datetime',
                                                                                               '-created_at')
    context = {
        'schedules': schedules
    }
    return render(request, 'core/my_schedule.html', context)


@employee_required
def employee_course_detail_view(request, course_id):
    course = get_object_or_404(TrainingCourse, pk=course_id)
    schedules = Schedule.objects.filter(course=course).select_related('client').order_by('-created_at')

    # Handle status update POST request
    if request.method == 'POST' and 'update_status' in request.POST:
        status_form = UpdateScheduleStatusForm(request.POST)
        if status_form.is_valid():
            schedule_id = status_form.cleaned_data['schedule_id']
            new_status = status_form.cleaned_data['status']
            try:
                schedule_to_update = Schedule.objects.get(id=schedule_id, course=course)
                schedule_to_update.status = new_status
                schedule_to_update.save(update_fields=['status', 'updated_at'])
                messages.success(request, f"Status updated for {schedule_to_update.client.full_name}.")
                # Redirect back to the same page to show updated status
                return redirect('employee_course_detail', course_id=course.id)
            except Schedule.DoesNotExist:
                messages.error(request, "Schedule not found.")
            except Exception as e:
                messages.error(request, f"Error updating status: {e}")
        else:

            messages.error(request, "Invalid status update request.")

    # Prepare forms for each schedule item in the template context
    schedule_forms = []
    for schedule in schedules:
        form = UpdateScheduleStatusForm(initial={'status': schedule.status, 'schedule_id': schedule.id})
        schedule_forms.append({'schedule': schedule, 'form': form})

    context = {
        'course': course,
        'schedule_forms': schedule_forms,
    }
    return render(request, 'core/employee_course_detail.html', context)


@employee_required
def edit_course_view(request, course_id):
    course = get_object_or_404(TrainingCourse, pk=course_id)
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.name}' updated successfully.")
            return redirect('manage_courses')  # Redirect to the list view after saving
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TrainingCourseForm(instance=course)

    context = {
        'form': form,
        'course': course,  # Pass course for context (e.g., title)
    }
    return render(request, 'core/edit_course.html', context)


@employee_required
def manage_clients_view(request):
    clients = ClientProfile.objects.select_related('user').all().order_by('user__last_name', 'user__first_name')
    context = {
        'clients': clients,
    }
    return render(request, 'core/manage_clients.html', context)

@employee_required
def issued_certificates_view(request):
    certificates = Certificate.objects.select_related(
        'client', 'certification_type'
    ).all().order_by('-issue_date')
    context = {
        'certificates': certificates,
    }
    return render(request, 'core/issued_certificates.html', context)


@employee_required
def client_detail_view(request, client_user_id):
    client_user = get_object_or_404(CustomUser, pk=client_user_id, is_employee=False)
    try:
        client_profile = client_user.client_profile
    except ClientProfile.DoesNotExist:
        client_profile = None

    # Fetch related data
    client_certificates = Certificate.objects.filter(client=client_user).select_related('certification_type').order_by('-issue_date')
    client_schedules = Schedule.objects.filter(client=client_user).select_related('course').order_by('-created_at')

    context = {
        'client_user': client_user,
        'client_profile': client_profile,
        'certificates': client_certificates,
        'schedules': client_schedules,
    }
    return render(request, 'core/client_detail.html', context)

