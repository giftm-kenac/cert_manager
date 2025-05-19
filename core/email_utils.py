import threading
import datetime
import qrcode
import io
import os
from PIL import Image, ImageDraw, ImageFont

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.core.files.base import ContentFile
from django.http import HttpResponse



class EmailThread(threading.Thread):
    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        try:
            self.email.send(fail_silently=False)
            print(f"Email sent successfully via thread to: {self.email.to}")
        except Exception as e:
            print(f"Error sending email via thread to {self.email.to}: {e}")


def generate_certificate_image_with_details(certificate):
    cert_type = certificate.certification_type
    client = certificate.client

    if not cert_type.template_image:
        raise ValueError(f"Template image missing for Certification Type: {cert_type.name}")

    try:
        template_img = Image.open(cert_type.template_image.path).convert("RGBA")
        draw = ImageDraw.Draw(template_img)

        recipient_name = client.get_full_name() if hasattr(client, 'get_full_name') else str(client) # Adapt as per your client model
        issue_date_str = f"Issued on: {certificate.issue_date.strftime('%B %d, %Y')}"
        certificate_id_str = f"ID: {certificate.id}" # Assuming certificate.id is UUID, convert to str if not already

        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        # Ensure 'core:verify_certificate' is the correct URL name in your 'core' app's urls.py
        verify_url_path = reverse('core:verify_certificate', kwargs={'certificate_id': str(certificate.id)})
        qr_code_data = site_url + verify_url_path

        font_name_pil = None
        font_date_pil = None
        font_cert_id_pil = None
        common_fonts = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Verdana.ttf", "Helvetica.ttf"] # Added Helvetica
        font_path_regular = None
        font_path_bold = None

        # Attempt to find a usable system font
        for font_name_try in common_fonts:
            try:
                # Test with a small size
                ImageFont.truetype(font_name_try, 10)
                font_path_regular = font_name_try
                # Try to find a bold variant
                base, ext = os.path.splitext(font_name_try)
                # Common bold naming conventions
                bold_variants_to_try = [f"{base}b{ext}", f"{base}-Bold{ext}", f"{base}_Bold{ext}", f"{base}bd{ext}", f"{base}-Bd{ext}"]
                font_path_bold = font_path_regular # Default to regular if bold not found
                for bold_variant in bold_variants_to_try:
                    try:
                        ImageFont.truetype(bold_variant, 10)
                        font_path_bold = bold_variant
                        break
                    except IOError:
                        continue
                break # Found a regular font, exit loop
            except IOError:
                continue

        try:
            if font_path_regular:
                font_name_pil = ImageFont.truetype(font_path_bold or font_path_regular, cert_type.name_font_size)
                font_date_pil = ImageFont.truetype(font_path_regular, cert_type.date_font_size)
                font_cert_id_pil = ImageFont.truetype(font_path_regular, cert_type.cert_id_font_size)
            else:
                print(f"Warning: Could not find common fonts for cert {certificate.id}. Using default bitmap font.")
                # Fallback to Pillow's default bitmap font if no TTF found
                font_name_pil = ImageFont.load_default()
                font_date_pil = ImageFont.load_default()
                font_cert_id_pil = ImageFont.load_default()
                # Note: Default font does not support size parameter in load_default() directly for older Pillow.
                # If using newer Pillow, size might be settable or use truetype with a bundled basic font.
        except IOError as font_err:
            # This should ideally not be reached if the fallback to load_default() is effective
            raise FileNotFoundError(f"Error loading fonts: {font_err}. Ensure font files are accessible or Pillow's default font can be used.")


        draw.text((cert_type.name_x, cert_type.name_y), recipient_name, fill=cert_type.name_color, font=font_name_pil)
        draw.text((cert_type.date_x, cert_type.date_y), issue_date_str, fill=cert_type.date_color, font=font_date_pil)
        draw.text((cert_type.cert_id_x, cert_type.cert_id_y), certificate_id_str, fill=cert_type.cert_id_color, font=font_cert_id_pil)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        qr_img_pil = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

        # Resize QR code using Resampling.LANCZOS for better quality
        qr_img_pil = qr_img_pil.resize((cert_type.qr_code_size, cert_type.qr_code_size), Image.Resampling.LANCZOS)

        template_img.paste(qr_img_pil, (cert_type.qr_code_x, cert_type.qr_code_y), qr_img_pil)

        buffer = io.BytesIO()
        template_img.save(buffer, format='PNG')
        buffer.seek(0)

        file_name = f'cert_{certificate.id}.png'
        certificate.generated_certificate_image.save(file_name, ContentFile(buffer.getvalue()), save=False) # Save=False, will be saved by caller or view

        # It's generally better to let the calling view/task handle the actual model save.
        # certificate.save(update_fields=['generated_certificate_image'])

        buffer.close()
        template_img.close()
        # No return needed as it saves to the field

    except Exception as e:
        print(f"Error generating certificate image for {certificate.id}: {e}")
        raise # Re-raise the exception to be handled by the caller


def render_certificate_to_pdf(certificate):
    if not certificate.generated_certificate_image or not certificate.generated_certificate_image.path:
        try:
            print(f"Attempting to generate missing image for PDF: {certificate.id}")
            generate_certificate_image_with_details(certificate) # This will save to the field
            certificate.save(update_fields=['generated_certificate_image']) # Explicitly save the model field change
            certificate.refresh_from_db(fields=['generated_certificate_image']) # Ensure path is updated
            if not certificate.generated_certificate_image or not certificate.generated_certificate_image.path:
                raise ValueError("Failed to generate or find certificate image path after attempt.")
        except Exception as e:
            print(f"Failed to generate image on-the-fly for PDF for cert {certificate.id}: {e}")
            return None

    try:
        img = Image.open(certificate.generated_certificate_image.path)
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF', resolution=100.0, save_all=False) # save_all=False for single image PDF
        pdf_buffer.seek(0)
        img.close()

        # Return the PDF content as bytes, not an HttpResponse here
        # The email function will handle creating the attachment
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_content

    except FileNotFoundError:
        print(f"Error: Generated image file not found for cert {certificate.id} at path {certificate.generated_certificate_image.path}")
        return None
    except Exception as e:
        print(f"Error converting image to PDF for cert {certificate.id}: {e}")
        return None

# --- Email Sending Functions ---

def send_verification_email_html(verification_code, to_email, fullname):
    subject = 'Verify Your Account - Certificate Portal'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'fullname': fullname,
        'verification_code': verification_code,
        'year': datetime.date.today().year,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
        'site_url': getattr(settings, 'SITE_URL', ''),
    }
    html_content = render_to_string('users/email/account_verification.html', context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
        email.attach_alternative(html_content, "text/html")
        EmailThread(email).start()
    except Exception as e:
        print(f"Error preparing verification email for {to_email}: {e}")


def send_employee_welcome_email_html(to_email, fullname, password, login_url_name='login'):
    subject = f'Welcome to {getattr(settings, "SITE_NAME", "Our Platform")} - Employee Account'
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        actual_login_url = settings.SITE_URL + reverse(login_url_name)
    except Exception:
        actual_login_url = settings.SITE_URL + "/users/login/"

    context = {
        'fullname': fullname,
        'email': to_email,
        'password': password,
        'login_url': actual_login_url,
        'year': datetime.date.today().year,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
    }
    html_content = render_to_string('core/email/employee_welcome.html', context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
        email.attach_alternative(html_content, "text/html")
        EmailThread(email).start()
    except Exception as e:
        print(f"Error preparing employee welcome email for {to_email}: {e}")


def send_certificate_issued_email_html(to_email, fullname, certificate_name, certificate_instance, verification_url_name='core:verify_certificate'):
    subject = f'Your Certificate Has Been Issued: {certificate_name}'
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        actual_verification_url = settings.SITE_URL + reverse(verification_url_name, kwargs={'certificate_id': str(certificate_instance.id)})
    except Exception as e:
        print(f"Error generating verification URL for email: {e}")
        actual_verification_url = settings.SITE_URL

    context = {
        'fullname': fullname,
        'certificate_name': certificate_name,
        'verification_url': actual_verification_url,
        'year': datetime.date.today().year,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
        'certificate_id': str(certificate_instance.id)
    }
    html_content = render_to_string('core/email/certificate_issued.html', context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
        email.attach_alternative(html_content, "text/html")

        pdf_content_bytes = render_certificate_to_pdf(certificate_instance)
        if pdf_content_bytes:
            pdf_filename = f"Certificate_{certificate_instance.certification_type.name.replace(' ', '_').replace('/', '-')}_{certificate_instance.id}.pdf"
            email.attach(pdf_filename, pdf_content_bytes, 'application/pdf')
        else:
            print(f"Could not generate PDF for attachment for cert {certificate_instance.id}. Email sent without PDF.")

        EmailThread(email).start()
    except Exception as e:
        print(f"Error preparing or sending certificate issued email for {to_email}: {e}")


def send_event_registration_confirmation_email(user_email, event):
    subject = f"Confirmation: You're Registered for {event.name}!"
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        event_public_url = settings.SITE_URL + reverse('core:public_event_register', kwargs={'event_slug': event.slug})
    except Exception:
        event_public_url = settings.SITE_URL

    context = {
        'event_name': event.name,
        'event_date': event.date,
        'event_time': event.time,
        'event_venue': event.venue,
        'user_email': user_email,
        'event_public_url': event_public_url,
        'site_url': settings.SITE_URL,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/email/event_registration_confirmation.html', context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
        email.attach_alternative(html_content, "text/html")
        EmailThread(email).start()
    except Exception as e:
        print(f"Error preparing event registration confirmation for {user_email}: {e}")


def send_new_user_credentials_event_email(user, password, event, login_url_name='login'):
    subject = f"Welcome to {getattr(settings, 'SITE_NAME', 'Our Platform')}! Your Account for {event.name}"
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        actual_login_url = settings.SITE_URL + reverse(login_url_name)
    except Exception:
        actual_login_url = settings.SITE_URL + "/users/login/"

    context = {
        'user_email': user.email,
        'fullname': user.get_full_name() if hasattr(user, 'get_full_name') else user.email,
        'password': password,
        'event_name': event.name,
        'login_url': actual_login_url,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
        'site_url': settings.SITE_URL,
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/email/new_user_credentials_event.html', context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
        email.attach_alternative(html_content, "text/html")
        EmailThread(email).start()
    except Exception as e:
        print(f"Error preparing new user credentials email for {user.email}: {e}")


def send_event_notification_to_registrants(event, subject, message_body_html, recipient_list):
    from_email = settings.DEFAULT_FROM_EMAIL

    context = {
        'event_name': event.name,
        'message_body_html': message_body_html,
        'site_name': getattr(settings, 'SITE_NAME', 'Our Platform'),
        'site_url': settings.SITE_URL,
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/email/event_custom_notification_wrapper.html', context)
    text_content = strip_tags(message_body_html)

    try:
        if recipient_list:
            # For privacy and to handle large lists better, send one email with recipients in BCC.
            # Some email backends might have limits on BCC, or you might prefer individual emails in a loop.
            email = EmailMultiAlternatives(subject, text_content, from_email, bcc=recipient_list)
            email.attach_alternative(html_content, "text/html")
            EmailThread(email).start()
        else:
            print("No recipients for event notification.")

    except Exception as e:
        print(f"Error preparing event notification for event {event.name}: {e}")
