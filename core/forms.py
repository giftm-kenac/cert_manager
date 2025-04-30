from django import forms
from django.core.exceptions import ValidationError

from .models import CertificationType, TrainingCourse, Certificate, Schedule, Skill  # Import Skill
from users.models import CustomUser
import uuid


class CertificationTypeForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = CertificationType
        fields = [
            'name', 'description', 'issuing_organization', 'template_image',
            'duration_days', 'is_active',
            'earning_criteria', 'skills',
            'name_x', 'name_y', 'name_font_size', 'name_color',
            'date_x', 'date_y', 'date_font_size', 'date_color',
            'cert_id_x', 'cert_id_y', 'cert_id_font_size', 'cert_id_color',
            'qr_code_x', 'qr_code_y', 'qr_code_size',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'issuing_organization': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'template_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'earning_criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
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
            'earning_criteria': 'Describe how this certificate is obtained.',
            'skills': 'Select the skills associated with this certification.'
        }


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['name', 'description', 'certification_type', 'instructor',
                  'start_date', 'end_date', 'location', 'price', 'delivery_method',
                  'cover_image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'certification_type': forms.Select(attrs={'class': 'form-control select2'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            # Updated widgets for start_date and end_date
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control select2'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IssueCertificateForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_employee=False, is_verified=True).select_related(
            'client_profile').order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-control select2', 'required': True}),
        label="Client",
        empty_label="-- Select Client --"
    )
    certification_type = forms.ModelChoiceField(
        queryset=CertificationType.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control select2', 'required': True}),
        label="Certification Type",
        empty_label="-- Select Type --"
    )
    issue_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control drgpicker', 'type': 'text'}),
        # Keep Date picker for single date
        help_text="Defaults to today if left blank."
    )


class ScheduleForm(forms.Form):
    event_datetime = forms.DateTimeField(
        label="Preferred Date and Time",
        # Updated widget for event_datetime
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True})
    )
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)


class UpdateScheduleStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Schedule.STATUS_CHOICES,
                               widget=forms.Select(attrs={'class': 'form-control form-control-sm'}))
    schedule_id = forms.IntegerField(widget=forms.HiddenInput())


class VerifyByIdForm(forms.Form):
    certificate_id = forms.UUIDField(
        label="Certificate ID",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter Certificate ID'})
    )


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter skill name'}),
        }


class BulkClientUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Select Excel File (.xlsx)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': '.xlsx'}),
        help_text='File must have columns: Email, FirstName, LastName, PhoneNumber (optional), Organization ('
                  'optional), Address (optional), City (optional), Country (optional), DOB (optional, YYYY-MM-DD), '
                  'Gender (optional)'
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith('.xlsx'):
                raise ValidationError("Invalid file type. Only .xlsx files are allowed.")
        return file


class BulkIssueCertificateForm(forms.Form):
    certification_type = forms.ModelChoiceField(
        queryset=CertificationType.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control select2', 'required': True}),
        label="Certification Type to Issue",
        empty_label="-- Select Type --"
    )
    issue_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control drgpicker', 'type': 'text'}),
        help_text="Optional. Defaults to today if left blank."
    )
    email_file = forms.FileField(
        label='Select Excel File (.xlsx) with Emails',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': '.xlsx'}),
        help_text='File must have a header row with at least one column named "Email".'
    )

    def clean_email_file(self):
        file = self.cleaned_data.get('email_file')
        if file:
            if not file.name.endswith('.xlsx'):
                raise ValidationError("Invalid file type. Only .xlsx files are allowed.")
        return file