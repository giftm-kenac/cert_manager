from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.client_register_view, name='client_register'),
    path('login/', user_views.user_login_view, name='user_login'),
    path('logout/', user_views.user_logout_view, name='user_logout'),
    path('verify/', user_views.verify_account_view, name='verify_account'),
    path('dashboard/', core_views.client_dashboard_view, name='client_dashboard'),
    path('my-certificates/', core_views.my_certificates_view, name='my_certificates'),
    path('my-schedule/', core_views.my_schedule_view, name='my_schedule'),
    path('courses/', core_views.available_courses_view, name='available_courses'),
    path('courses/<int:course_id>/', core_views.course_detail_view, name='course_detail'),
    path('certificate/<uuid:certificate_id>/download-image/', core_views.download_certificate_image_view, name='download_certificate_image'),
    path('certificate/<uuid:certificate_id>/download-pdf/', core_views.download_certificate_pdf_view, name='download_certificate_pdf'),
    path('my-event-registrations/<int:registration_pk>/cancel/', core_views.UserCancelEventRegistrationView.as_view(), name='user_cancel_event_registration'),
    path('employee/dashboard/', core_views.employee_dashboard_view, name='employee_dashboard'),
    path('employee/employees/', user_views.manage_employees_view, name='manage_employees'),
    path('employee/clients/', core_views.manage_clients_view, name='manage_clients'),
    path('employee/clients/<int:client_user_id>/', core_views.client_detail_view, name='client_detail'),
    path('employee/cert-types/', core_views.manage_certification_types_view, name='manage_certification_types'),
    path('employee/cert-types/add/', core_views.add_certification_type_view, name='add_certification_type'),
    path('employee/cert-types/<int:certification_type_id>/edit/', core_views.edit_certification_type_view, name='edit_certification_type'),
    path('employee/courses/', core_views.manage_courses_view, name='manage_courses'),
    path('employee/courses/<int:course_id>/edit/', core_views.edit_course_view, name='edit_course'),
    path('employee/courses/<int:course_id>/details/', core_views.employee_course_detail_view, name='employee_course_detail'),
    path('employee/issue-certificate/', core_views.issue_certificate_view, name='issue_certificate'),
    path('employee/bulk-issue-certificates/', core_views.bulk_issue_certificates_view, name='bulk_issue_certificates'),
    path('employee/skills/', core_views.manage_skills_view, name='manage_skills'),
    path('employee/skills/<int:skill_id>/edit/', core_views.edit_skill_view, name='edit_skill'),
    path('employee/skills/<int:skill_id>/delete/', core_views.delete_skill_view, name='delete_skill'),
    path('employee/issued-certificates/', core_views.issued_certificates_view, name='issued_certificates'),
    path('employee/events/', core_views.EventListView.as_view(), name='event_list_admin'),
    path('employee/events/create/', core_views.EventCreateView.as_view(), name='event_create'),
    path('employee/events/<int:pk>/edit/', core_views.EventUpdateView.as_view(), name='event_edit'),
    path('employee/events/<int:pk>/detail/', core_views.EventDetailAdminView.as_view(), name='event_detail_admin'),
    path('employee/events/<int:event_pk>/cancel/', core_views.AdminCancelEventView.as_view(), name='admin_cancel_event'),
    path('employee/events/<int:event_pk>/registrations/', core_views.manage_event_registrations, name='manage_event_registrations'),
    path('employee/events/<int:event_pk>/issue-certificates/', core_views.issue_event_certificates, name='issue_event_certificates'),
    path('employee/events/<int:event_pk>/send-notification/', core_views.send_event_notification_view, name='send_event_notification'),
    path('verify/<uuid:certificate_id>/', core_views.verify_certificate_view, name='verify_certificate'),
    path('verify-by-id/', core_views.verify_certificate_by_id_input_view, name='verify_certificate_by_id'),
    path('events/<slug:event_slug>/register/', core_views.PublicEventRegisterView.as_view(), name='public_event_register'),
    path('events/<slug:event_slug>/registration-success/', core_views.EventRegistrationSuccessView.as_view(), name='event_registration_success'),
    path('', user_views.user_login_view, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)