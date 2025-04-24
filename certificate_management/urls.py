# urls.py (Project's root urls.py)

from django.contrib import admin
from django.urls import path, include # Import include
from django.conf import settings
from django.conf.urls.static import static

# Import app view modules
from users import views as user_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Authentication URLs (from users.views) ---
    path('register/', user_views.client_register_view, name='client_register'),
    path('login/', user_views.user_login_view, name='user_login'),
    path('logout/', user_views.user_logout_view, name='user_logout'),
    path('verify/', user_views.verify_account_view, name='verify_account'),

    # --- Client Portal URLs (from core.views) ---
    path('dashboard/', core_views.client_dashboard_view, name='client_dashboard'),
    path('my-certificates/', core_views.my_certificates_view, name='my_certificates'),
    path('my-schedule/', core_views.my_schedule_view, name='my_schedule'),
    path('courses/', core_views.available_courses_view, name='available_courses'),
    path('courses/<int:course_id>/', core_views.course_detail_view, name='course_detail'),
    path('certificate/<uuid:certificate_id>/download/', core_views.download_certificate_image_view,
         name='download_certificate'),


    # --- Employee/Admin URLs ---
    # Employee Dashboard (from core.views)
    path('employee/dashboard/', core_views.employee_dashboard_view, name='employee_dashboard'),
    # Employee Management (from users.views)
    path('employee/employees/', user_views.manage_employees_view, name='manage_employees'),
    path('employee/clients/', core_views.manage_clients_view, name='manage_clients'),
    path('employee/clients/<int:client_user_id>/', core_views.client_detail_view, name='client_detail'),
    # Certificate/Course Management (from core.views)
    path('employee/cert-types/', core_views.manage_certification_types_view, name='manage_certification_types'),
    path('employee/cert-types/add/', core_views.add_certification_type_view, name='add_certification_type'),
    path('employee/cert-types/<int:certification_type_id>/edit/', core_views.edit_certification_type_view,
         name='edit_certification_type'),
    path('employee/courses/', core_views.manage_courses_view, name='manage_courses'),
    path('employee/courses/<int:course_id>/edit/', core_views.edit_course_view, name='edit_course'),
    path('employee/courses/<int:course_id>/details/', core_views.employee_course_detail_view,
         name='employee_course_detail'),
    path('employee/issue-certificate/', core_views.issue_certificate_view, name='issue_certificate'),
    path('employee/issued-certificates/', core_views.issued_certificates_view, name='issued_certificates'),

    # --- Public Verification URL (from core.views) ---
    path('verify/<uuid:certificate_id>/', core_views.verify_certificate_view, name='verify_certificate'),
    path('verify-by-id/', core_views.verify_certificate_by_id_input_view, name='verify_certificate_by_id'),

    # --- Default Home ---
    path('', user_views.user_login_view, name='home'), # Redirects to login

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static files are usually handled by whitenoise or webserver in production
    # This line is often only needed for development runserver
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
