# core/utils.py

import threading
import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings  # To get sender email


class EmailThread(threading.Thread):
    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        self.email.send(fail_silently=False)  # Set fail_silently=True in production?


def send_verification_email_html(verification_code, to_email, fullname):
    subject = 'Verify Your Account - Certificate Portal'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'fullname': fullname,
        'verification_code': verification_code,
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/account_verification.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    EmailThread(email).start()


def send_employee_welcome_email_html(to_email, fullname, password, login_url):
    subject = 'Welcome to the Certificate Portal - Employee Account'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'fullname': fullname,
        'email': to_email,
        'password': password,
        'login_url': login_url,
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/employee_welcome.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    EmailThread(email).start()


def send_certificate_issued_email_html(to_email, fullname, certificate_name, verification_url):
    subject = f'Your Certificate Has Been Issued: {certificate_name}'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'fullname': fullname,
        'certificate_name': certificate_name,
        'verification_url': verification_url,  # URL to view/verify the cert
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/certificate_issued.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    EmailThread(email).start()
