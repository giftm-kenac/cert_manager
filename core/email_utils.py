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
from django.core.files.base import ContentFile
from django.urls import reverse  # Import reverse for get_absolute_url


class EmailThread(threading.Thread):
    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        self.email.send(fail_silently=False)


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

    email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
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

    email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
    email.attach_alternative(html_content, "text/html")
    EmailThread(email).start()


def send_certificate_issued_email_html(to_email, fullname, certificate_name, verification_url):
    subject = f'Your Certificate Has Been Issued: {certificate_name}'
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'fullname': fullname,
        'certificate_name': certificate_name,
        'verification_url': verification_url,
        'year': datetime.date.today().year,
    }
    html_content = render_to_string('core/certificate_issued.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
    email.attach_alternative(html_content, "text/html")
    EmailThread(email).start()


def generate_certificate_image_with_details(certificate):
    cert_type = certificate.certification_type
    client = certificate.client

    if not cert_type.template_image:
        raise ValueError(f"Template image missing for Certification Type: {cert_type.name}")

    try:
        template_img = Image.open(cert_type.template_image.path).convert("RGBA")
        draw = ImageDraw.Draw(template_img)

        recipient_name = client.full_name
        issue_date_str = f"{certificate.issue_date.strftime('%B %d, %Y')}"
        certificate_id_str = f"ID: {certificate.id}"

        # Ensure QR code data uses the absolute URL
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')  # Use settings or fallback
        verify_url_path = reverse('verify_certificate', kwargs={'certificate_id': certificate.id})
        qr_code_data = site_url + verify_url_path


        font_name = None
        font_date = None
        font_cert_id = None
        common_fonts = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Verdana.ttf"]
        font_path_regular = None
        font_path_bold = None

        for font_name_try in common_fonts:
            try:
                test_font = ImageFont.truetype(font_name_try, 10)
                font_path_regular = font_name_try
                base, ext = os.path.splitext(font_name_try)
                bold_variant = f"{base}-Bold{ext}"
                try:
                    ImageFont.truetype(bold_variant, 10)
                    font_path_bold = bold_variant
                except IOError:
                    font_path_bold = font_path_regular
                break
            except IOError:
                continue

        try:
            if font_path_regular:
                font_name = ImageFont.truetype(font_path_bold or font_path_regular, cert_type.name_font_size)
                font_date = ImageFont.truetype(font_path_regular, cert_type.date_font_size)
                font_cert_id = ImageFont.truetype(font_path_regular, cert_type.cert_id_font_size)
            else:
                # Fallback to Pillow's default bitmap font if no system fonts found
                print(f"Warning: Could not find common fonts for cert {certificate.id}. Using default bitmap font.")
                font_name = ImageFont.load_default(size=cert_type.name_font_size)  # Approximate size
                font_date = ImageFont.load_default(size=cert_type.date_font_size)
                font_cert_id = ImageFont.load_default(size=cert_type.cert_id_font_size)
        except IOError as font_err:

            raise FileNotFoundError(f"Error loading fonts: {font_err}")

        draw.text((cert_type.name_x, cert_type.name_y), recipient_name, fill=cert_type.name_color, font=font_name)
        draw.text((cert_type.date_x, cert_type.date_y), issue_date_str, fill=cert_type.date_color, font=font_date)
        draw.text((cert_type.cert_id_x, cert_type.cert_id_y), certificate_id_str, fill=cert_type.cert_id_color,
                  font=font_cert_id)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        qr_img_pil = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        qr_img_pil = qr_img_pil.resize((cert_type.qr_code_size, cert_type.qr_code_size), Image.Resampling.LANCZOS)
        template_img.paste(qr_img_pil, (cert_type.qr_code_x, cert_type.qr_code_y), qr_img_pil)

        buffer = io.BytesIO()
        template_img.save(buffer, format='PNG')
        buffer.seek(0)

        template_img.close()

        # Return the buffer containing the image data
        return buffer

    except Exception as e:
        print(f"Error generating certificate image for {certificate.id}: {e}")
        raise
