# core/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import uuid

from users.models import TimeStampedModel

class CertificationType(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    issuing_organization = models.CharField(max_length=200, default="Your Organization Name")
    template_image = models.ImageField(
        upload_to='certificate_templates/',
        blank=True,
        null=True
    )
    duration_days = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Price might be more relevant per course

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
                 pass # It will be generated on the next save

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
        ('REQUESTED', 'Requested'), # Changed default
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