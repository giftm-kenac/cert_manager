# core/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import uuid

from django.utils.text import slugify

from users.models import TimeStampedModel, EmployeeProfile, CustomUser


class Skill(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CertificationType(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    issuing_organization = models.CharField(max_length=200, default="Your Organization Name")
    template_image = models.ImageField(
        upload_to='certificate_templates/',
        blank=True,
        null=True,
        help_text="Background image/design for the certificate."
    )
    duration_days = models.PositiveIntegerField(blank=True, null=True,
                                                help_text="Optional: Validity duration in days from issue date.")
    is_active = models.BooleanField(default=True)
    earning_criteria = models.TextField(blank=True, null=True, help_text="Describe how this certificate is earned (e.g., exam details, course completion).")
    skills = models.ManyToManyField(Skill, blank=True, related_name="certification_types")

    # Recipient Name
    name_x = models.PositiveIntegerField(default=50, help_text="X coordinate for recipient name")
    name_y = models.PositiveIntegerField(default=200, help_text="Y coordinate for recipient name")
    name_font_size = models.PositiveIntegerField(default=30, help_text="Font size for recipient name")
    name_color = models.CharField(max_length=7, default="#000000", help_text="Hex color code for name (e.g., #000000)")

    # Issue Date
    date_x = models.PositiveIntegerField(default=50, help_text="X coordinate for issue date")
    date_y = models.PositiveIntegerField(default=300, help_text="Y coordinate for issue date")
    date_font_size = models.PositiveIntegerField(default=14, help_text="Font size for issue date")
    date_color = models.CharField(max_length=7, default="#333333", help_text="Hex color code for date")

    # Certificate ID
    cert_id_x = models.PositiveIntegerField(default=50, help_text="X coordinate for certificate ID")
    cert_id_y = models.PositiveIntegerField(default=350, help_text="Y coordinate for certificate ID")
    cert_id_font_size = models.PositiveIntegerField(default=10, help_text="Font size for certificate ID")
    cert_id_color = models.CharField(max_length=7, default="#555555", help_text="Hex color code for ID")

    # QR Code
    qr_code_x = models.PositiveIntegerField(default=600, help_text="X coordinate for QR Code (top-left)")
    qr_code_y = models.PositiveIntegerField(default=300, help_text="Y coordinate for QR Code (top-left)")
    qr_code_size = models.PositiveIntegerField(default=100, help_text="Size (width & height) of QR Code in pixels")

    def __str__(self):
        return self.name


class Certificate(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        limit_choices_to={'is_employee': False}
    )
    certification_type = models.ForeignKey(CertificationType, on_delete=models.PROTECT)
    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(blank=True, null=True)
    qr_code_data = models.URLField(max_length=500, blank=True)
    generated_certificate_image = models.ImageField(
        upload_to='generated_certificates/',
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('client', 'certification_type')
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.certification_type.name} for {self.client.full_name}"

    def get_absolute_url(self):
        return reverse('verify_certificate', kwargs={'certificate_id': self.id})

    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.certification_type.duration_days and not self.expiry_date:
            self.expiry_date = self.issue_date + timezone.timedelta(days=self.certification_type.duration_days)

        # Generate QR code data URL only after we definitely have an ID
        if not self.qr_code_data and self.pk:
            site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            try:
                verify_url_path = reverse('verify_certificate', kwargs={'certificate_id': self.id})
                self.qr_code_data = site_url + verify_url_path
            except Exception:
                pass  # It will be generated on the next save

        super().save(*args, **kwargs)

        # If QR code data wasn't generated on the first save (because pk was None), try again
        if is_new and not self.qr_code_data and self.pk:
            self.save(update_fields=['qr_code_data'])

        super().save(*args, **kwargs)

        # If QR code data was just generated on this save, save again
        if is_new and not self.qr_code_data:
            self.save(update_fields=['qr_code_data'])


class TrainingCourse(TimeStampedModel):
    DELIVERY_CHOICES = [
        ('ONLINE_EXAM', 'Online Exam'),
        ('PROCTORED_EXAM', 'Proctored Exam'),
        ('IN_PERSON', 'In-Person Training/Exam'),
        ('BADGE_ONLY', 'Digital Badge Only'),
        ('ONLINE_COURSE', 'Online Course (Self-paced)'),
        ('VILT', 'Virtual Instructor-Led Training'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    certification_type = models.ForeignKey(
        CertificationType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses'
    )
    instructor = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_method = models.CharField(max_length=50, choices=DELIVERY_CHOICES, blank=True, null=True)
    cover_image = models.ImageField(
        upload_to='course_covers/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class Schedule(TimeStampedModel):
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),  # Changed default
        ('SCHEDULED', 'Scheduled/Confirmed'),
        ('ATTENDED', 'Attended'),
        ('CANCELLED_BY_USER', 'Cancelled by User'),
        ('CANCELLED_BY_ADMIN', 'Cancelled by Admin'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'is_employee': False}
    )
    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    # Renamed to reflect the chosen date/time for the event/exam/training
    event_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        # Allow multiple schedules for the same course if event_datetime differs
        unique_together = ('client', 'course', 'event_datetime')
        ordering = ['-event_datetime', '-created_at']

    def __str__(self):
        event_time = self.event_datetime.strftime('%Y-%m-%d %H:%M') if self.event_datetime else "Unscheduled"
        return f"{self.client.full_name} - {self.course.name} ({event_time} - {self.get_status_display()})"



class Event(models.Model):
    """
    Represents an event that users can register for.
    """
    name = models.CharField(max_length=255, help_text="The official name of the event.")
    description = models.TextField(help_text="A detailed description of the event.")
    venue = models.CharField(max_length=255, help_text="Physical or virtual location of the event.")
    date = models.DateField(help_text="Date of the event.")
    time = models.TimeField(help_text="Start time of the event.")

    certification_type = models.ForeignKey(
        CertificationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Certificate to be awarded upon completion/attendance (optional)."
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='created_events',
        limit_choices_to={'is_employee': True}, # Ensure only employees can create events
        help_text="Employee who created this event."
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="URL-friendly identifier. Auto-generated if left blank.")
    is_active = models.BooleanField(default=True, help_text="Controls if public registration is open.")
    max_attendees = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of allowed registrations (optional).")
    registration_deadline = models.DateTimeField(null=True, blank=True, help_text="Registrations close after this date/time (optional).")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{uuid.uuid4().hex[:6]}") # Add a short UUID to ensure uniqueness
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date', '-time']


class EventQuestion(models.Model):
    """
    A question defined for an event's registration form.
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text (Single Line)'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('textarea', 'Text Area (Multi-line)'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons (Single Choice)'),
        ('checkbox', 'Checkboxes (Multiple Choices Possible)'),
        ('number', 'Number'),
        ('date', 'Date'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, help_text="The question text (e.g., 'Full Name & Surname').")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, help_text="The type of input field for this question.")
    is_required = models.BooleanField(default=True, help_text="Is answering this question mandatory?")
    order = models.PositiveIntegerField(default=0, help_text="Order in which questions appear on the form.")

    def __str__(self):
        return f"{self.event.name} - Q{self.order}: {self.text[:50]}..."

    class Meta:
        ordering = ['event', 'order']


class EventQuestionOption(models.Model):
    """
    An option for a multiple-choice (select, radio, checkbox) EventQuestion.
    """
    question = models.ForeignKey(EventQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255, help_text="The text displayed for this option (e.g., 'Small', 'Visit to the Falls').")
    value = models.CharField(max_length=255, blank=True, help_text="The value stored if this option is selected (defaults to option_text if blank).")

    def __str__(self):
        return f"{self.question.text[:30]}... - Option: {self.option_text}"

    def get_value(self):
        return self.value if self.value else self.option_text

    class Meta:
        ordering = ['question', 'option_text']


class EventRegistration(models.Model):
    """
    Records a user's registration for a specific event.
    """
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('CONFIRMED', 'Confirmed'), # e.g., if payment or further action was needed
        ('CANCELLED_BY_USER', 'Cancelled by User'),
        ('CANCELLED_BY_ADMIN', 'Cancelled by Admin'),
        ('WAITLISTED', 'Waitlisted'),
        ('ATTENDED', 'Attended'),
        ('NOT_ATTENDED', 'Not Attended'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_registrations', help_text="The client who registered.")
    registration_date = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False, help_text="Marked by admin if the user attended the event.") # Can be deprecated if status 'ATTENDED' is used
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')

    # Unique constraint to prevent double registration for the same event by the same user
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.email} registered for {self.event.name}"


class EventRegistrationAnswer(models.Model):
    """
    Stores an answer to a specific EventQuestion for an EventRegistration.
    """
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(EventQuestion, on_delete=models.CASCADE, related_name='user_answers')

    # For text, textarea, select, radio, email, phone, number, date
    answer_text = models.TextField(blank=True, null=True, help_text="The user's answer for text-based or single-choice questions.")

    # For checkbox (multiple selections possible)
    # We store the selected EventQuestionOption(s)
    selected_options = models.ManyToManyField(
        EventQuestionOption,
        blank=True,
        related_name='answer_selections',
        help_text="For checkbox questions, links to the selected options."
    )

    def __str__(self):
        if self.answer_text:
            return f"Answer to '{self.question.text[:30]}...': {self.answer_text[:50]}..."
        elif self.selected_options.exists():
            options_str = ", ".join([opt.option_text for opt in self.selected_options.all()])
            return f"Answer to '{self.question.text[:30]}...': {options_str}"
        return f"No answer provided for '{self.question.text[:30]}...'"

    class Meta:
        # Ensures one answer per question per registration
        unique_together = ('registration', 'question')
        ordering = ['registration', 'question__order']