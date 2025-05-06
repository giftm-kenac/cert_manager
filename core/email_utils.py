# core/utils.py

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
from django.urls import reverse
from django.http import HttpResponse  # Import HttpResponse


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


def generate_certificate_image_with_details(certificate):
    cert_type = certificate.certification_type
    client = certificate.client

    if not cert_type.template_image:
        raise ValueError(f"Template image missing for Certification Type: {cert_type.name}")

    try:
        template_img = Image.open(cert_type.template_image.path).convert("RGBA")
        draw = ImageDraw.Draw(template_img)

        recipient_name = client.full_name
        issue_date_str = f"Issued on: {certificate.issue_date.strftime('%B %d, %Y')}"
        certificate_id_str = f"ID: {certificate.id}"
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
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
                print(f"Warning: Could not find common fonts for cert {certificate.id}. Using default bitmap font.")
                font_name = ImageFont.load_default(size=cert_type.name_font_size)
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
        # Save the final image as PNG into the buffer
        template_img.save(buffer, format='PNG')
        buffer.seek(0)

        # Save the generated PNG to the model field
        file_name = f'cert_{certificate.id}.png'
        certificate.generated_certificate_image.save(file_name, ContentFile(buffer.getvalue()),
                                                     save=True)  # save=True updates the instance

        buffer.close()
        template_img.close()

        # No need to return the buffer anymore as we save directly to the field

    except Exception as e:
        print(f"Error generating certificate image for {certificate.id}: {e}")
        raise


# --- Updated PDF Generation Function (from generated image) ---
def render_certificate_to_pdf(certificate):
    # 1. Ensure the generated image exists
    if not certificate.generated_certificate_image or not certificate.generated_certificate_image.path:
        # Optionally try to generate it if missing (might be slow)
        try:
            print(f"Regenerating missing image for PDF: {certificate.id}")
            generate_certificate_image_with_details(certificate)
            # Reload certificate instance to get the updated image path
            certificate.refresh_from_db(fields=['generated_certificate_image'])
            if not certificate.generated_certificate_image or not certificate.generated_certificate_image.path:
                raise ValueError("Failed to generate or find certificate image.")
        except Exception as e:
            print(f"Failed to generate image on-the-fly for PDF: {e}")
            return None  # Cannot create PDF without the image

    try:
        # 2. Open the generated PNG image using Pillow
        img = Image.open(certificate.generated_certificate_image.path)

        # 3. Ensure image is in RGB mode for PDF saving (if it was RGBA)
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # 4. Create an in-memory buffer for the PDF
        pdf_buffer = io.BytesIO()

        # 5. Save the image directly as PDF into the buffer
        img.save(pdf_buffer, format='PDF', resolution=100.0)  # Adjust resolution if needed
        pdf_buffer.seek(0)

        img.close()

        # 6. Create an HttpResponse with the PDF data
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        # pdf_filename = f"Certificate_{certificate.id}.pdf"
        # response['Content-Disposition'] = f'inline; filename="{pdf_filename}"' # Or 'attachment;'
        pdf_buffer.close()
        return response

    except FileNotFoundError:
        print(
            f"Error: Generated image file not found for cert {certificate.id} at path {certificate.generated_certificate_image.path}")
        return None
    except Exception as e:
        print(f"Error converting image to PDF for cert {certificate.id}: {e}")
        return None


# --- End Updated PDF Generation Function ---


# --- Updated Email Function to attach PDF ---
def send_certificate_issued_email_html(to_email, fullname, certificate_name, verification_url, certificate_instance):
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

    # --- Attach PDF ---
    try:
        pdf_response = render_certificate_to_pdf(certificate_instance)
        if pdf_response:
            pdf_filename = f"Certificate_{certificate_instance.certification_type.name.replace(' ', '_')}_{certificate_instance.id}.pdf"
            email.attach(pdf_filename, pdf_response.content, 'application/pdf')
        else:
            print(f"Could not generate PDF for attachment for cert {certificate_instance.id}")
    except Exception as pdf_err:
        print(f"Error attaching PDF to email for cert {certificate_instance.id}: {pdf_err}")
    # --- End Attach PDF ---

    EmailThread(email).start()
# --- End Updated Email Function ---
