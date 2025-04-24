# core/forms.py
from django import forms
from .models import CertificationType, TrainingCourse, Certificate, Schedule
from users.models import CustomUser


class CertificationTypeForm(forms.ModelForm):
    class Meta:
        model = CertificationType
        fields = [
            'name', 'description', 'issuing_organization', 'template_image',
            'duration_days', 'is_active',
            # Coordinate fields (excluding certificate title)
            'name_x', 'name_y', 'name_font_size', 'name_color',
            'date_x', 'date_y', 'date_font_size', 'date_color',
            'cert_id_x', 'cert_id_y', 'cert_id_font_size', 'cert_id_color',
            'qr_code_x', 'qr_code_y', 'qr_code_size',
        ]
        widgets = {
            # Existing fields
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'issuing_organization': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'template_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Coordinate fields
            'name_x': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'name_y': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'name_font_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'name_color': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'color'}),
            'date_x': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'date_y': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'date_font_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'date_color': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'color'}),
            'cert_id_x': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'cert_id_y': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'cert_id_font_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'cert_id_color': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'color'}),
            'qr_code_x': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'qr_code_y': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'qr_code_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }
        help_texts = {
            'name_color': 'E.g., #000000 for black',
            'date_color': 'E.g., #333333',
            'cert_id_color': 'E.g., #555555',
        }



class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['name', 'description', 'certification_type', 'instructor',
                  'start_date', 'end_date', 'location', 'price', 'delivery_method', 'cover_image','is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'certification_type': forms.Select(attrs={'class': 'form-control select2'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control ', 'type': 'datetime-local'}),
            # Use datetime picker class
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            # Use datetime picker class
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control select2'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IssueCertificateForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_employee=False, is_verified=True).select_related('client_profile'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Client"
    )
    certification_type = forms.ModelChoiceField(
        queryset=CertificationType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Certification Type"
    )
    issue_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        help_text="Defaults to today if left blank."
    )


class ScheduleForm(forms.Form):
    event_datetime = forms.DateTimeField(
        label="Preferred Date and Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
        # Use datetime picker class
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)


class UpdateScheduleStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Schedule.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control form-control-sm'}))
    schedule_id = forms.IntegerField(widget=forms.HiddenInput())


class VerifyByIdForm(forms.Form):
    certificate_id = forms.UUIDField(
        label="Certificate ID",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter Certificate ID'})
    )