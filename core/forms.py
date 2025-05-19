from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid # Retained from original, though not directly used in the provided form snippets

# Models from your application
from .models import (
    CertificationType,
    TrainingCourse,
    # Certificate, # Not directly used in these forms but might be in other parts of your original forms.py
    Schedule,
    Skill,
    Event,
    EventQuestion,
    EventQuestionOption,
    EventRegistration
)

from users.models import CustomUser


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
            'clientprofile').order_by('first_name', 'last_name'), # Assuming 'clientprofile' is the related_name from CustomUser to ClientProfile
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
        help_text="Defaults to today if left blank."
    )


class ScheduleForm(forms.Form):
    event_datetime = forms.DateTimeField(
        label="Preferred Date and Time",
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
        help_text='File must have columns: Email, FirstName, LastName, PhoneNumber (optional), Organization (optional), Address (optional), City (optional), Country (optional), DOB (optional, YYYY-MM-DD), Gender (optional)'
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

# --- Event Management Forms ---

class EventForm(forms.ModelForm):
    certification_type = forms.ModelChoiceField(
        queryset=CertificationType.objects.all(), # Assuming you want all, active or not, for admin selection
        required=False, # An event might not always issue a certificate
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Associated Certificate Type (Optional)"
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Event Date"
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), # Corrected fTimeInput to forms.TimeInput
        label="Event Start Time"
    )
    registration_deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Registration Deadline (Optional)"
    )

    class Meta:
        model = Event
        fields = [
            'name', 'description', 'venue', 'date', 'time',
            'certification_type', 'is_active', 'max_attendees',
            'registration_deadline'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_attendees': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'is_active': "Registration Open?",
            'max_attendees': "Max. Attendees (Optional)"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: If you want to ensure only active certification types can be linked
        # self.fields['certification_type'].queryset = CertificationType.objects.filter(is_active=True)
        self.fields['name'].widget.attrs['placeholder'] = 'e.g., Annual Tech Conference 2025'
        self.fields['venue'].widget.attrs['placeholder'] = 'e.g., Convention Center Hall A / Online via Zoom'


class EventQuestionForm(forms.ModelForm):
    class Meta:
        model = EventQuestion
        fields = ['text', 'field_type', 'is_required', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., What is your T-shirt size?'}),
            'field_type': forms.Select(attrs={'class': 'form-control select2'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }
        labels = {
            'field_type': "Question Type",
            'is_required': "Required?"
        }

class EventQuestionOptionForm(forms.ModelForm):
    class Meta:
        model = EventQuestionOption
        fields = ['option_text', 'value']
        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Small / Medium / Large'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., S / M / L (optional, uses text if blank)'}),
        }
        labels = {
            'option_text': "Display Text for Option",
            'value': "Stored Value (Optional)"
        }

EventQuestionFormSet = forms.inlineformset_factory(
    Event, EventQuestion, form=EventQuestionForm,
    fields=['text', 'field_type', 'is_required', 'order'],
    extra=1, can_delete=True, can_order=False, # Set can_order to True if you want to allow reordering via formset
    widgets={ # These widgets apply to the forms within the formset
        'text': forms.TextInput(attrs={'class': 'form-control form-control-sm mb-1', 'placeholder': 'Question Text'}),
        'field_type': forms.Select(attrs={'class': 'form-control form-control-sm select2 mb-1'}),
        'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input mb-1'}),
        'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm mb-1', 'placeholder': 'Order'}),
    }
)

# This formset is for managing options *within* a question form, typically nested.
# It might be simpler to manage options on a separate page or via a modal for each question.
EventQuestionOptionInlineFormSet = forms.inlineformset_factory(
    EventQuestion, EventQuestionOption, form=EventQuestionOptionForm,
    fields=['option_text', 'value'],
    extra=1, can_delete=True,
    widgets={
        'option_text': forms.TextInput(attrs={'class': 'form-control form-control-sm mb-1', 'placeholder': 'Option Display Text'}),
        'value': forms.TextInput(attrs={'class': 'form-control form-control-sm mb-1', 'placeholder': 'Option Value (optional)'}),
    }
)


class PublicEventRegistrationForm(forms.Form):
    user_email = forms.EmailField(
        label="Your Email Address",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Enter your primary email address'})
    )
    # Consider adding a fixed "Full Name" field if it's always required and not part of dynamic questions.
    # user_full_name = forms.CharField(label="Full Name", required=True, widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))


    def __init__(self, *args, **kwargs):
        event_questions = kwargs.pop('event_questions', None)
        super().__init__(*args, **kwargs)

        if event_questions:
            for question in event_questions:
                field_kwargs = {
                    'label': question.text,
                    'required': question.is_required,
                }

                field_name = f'question_{question.id}'
                attrs = {'class': 'form-control mb-3'}
                if question.field_type == 'radio' or question.field_type == 'checkbox':
                    attrs = {'class': 'form-check-input me-1'}


                if question.field_type == 'text':
                    field_kwargs['widget'] = forms.TextInput(attrs=attrs)
                    field = forms.CharField(**field_kwargs)
                elif question.field_type == 'email': # Dynamic email field if needed
                    field_kwargs['widget'] = forms.EmailInput(attrs=attrs)
                    field = forms.EmailField(**field_kwargs)
                elif question.field_type == 'phone':
                    attrs['type'] = 'tel'
                    field_kwargs['widget'] = forms.TextInput(attrs=attrs)
                    field = forms.CharField(**field_kwargs)
                elif question.field_type == 'textarea':
                    attrs['rows'] = 3
                    field_kwargs['widget'] = forms.Textarea(attrs=attrs)
                    field = forms.CharField(**field_kwargs)
                elif question.field_type == 'number':
                    field_kwargs['widget'] = forms.NumberInput(attrs=attrs)
                    field = forms.IntegerField(**field_kwargs)
                elif question.field_type == 'date':
                    attrs['type'] = 'date'
                    field_kwargs['widget'] = forms.DateInput(attrs=attrs)
                    field = forms.DateField(**field_kwargs)
                elif question.field_type in ['select', 'radio']:
                    choices = [(opt.get_value(), opt.option_text) for opt in question.options.all()]
                    if not question.is_required: # Add an empty choice for non-required select/radio
                        choices.insert(0, ('', '---------'))

                    if question.field_type == 'select':
                        field_kwargs['widget'] = forms.Select(attrs={'class': 'form-control select2 mb-3'}) # select2 for dropdown
                        field = forms.ChoiceField(choices=choices, **field_kwargs)
                    else: # radio
                        field_kwargs['widget'] = forms.RadioSelect(attrs={'class': 'form-check-input'}) # Default RadioSelect rendering
                        field = forms.ChoiceField(choices=choices, **field_kwargs)
                elif question.field_type == 'checkbox': # For multiple choice checkboxes
                    choices = [(opt.id, opt.option_text) for opt in question.options.all()]
                    field_kwargs['widget'] = forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}) # Default CheckboxSelectMultiple
                    field = forms.MultipleChoiceField(choices=choices, **field_kwargs)
                else: # Fallback
                    field_kwargs['widget'] = forms.TextInput(attrs=attrs)
                    field = forms.CharField(**field_kwargs)

                self.fields[field_name] = field


class EventAttendeeSelectionForm(forms.Form):
    attendees = forms.ModelMultipleChoiceField(
        queryset=EventRegistration.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Select Attendees to Issue Certificates To"
    )

    def __init__(self, *args, **kwargs):
        event_id = kwargs.pop('event_id', None)
        super().__init__(*args, **kwargs)
        if event_id:
            # Queryset for users who are marked as 'ATTENDED' for the given event.
            # Adjust status if you want to include 'CONFIRMED' etc.
            qs = EventRegistration.objects.filter(
                event_id=event_id,
                status='ATTENDED' # Typically, certificates are for those who attended
            ).select_related('user') # Optimize by selecting related user

            self.fields['attendees'].queryset = qs
            self.fields['attendees'].label_from_instance = \
                lambda obj: f"{obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else obj.user.email} (Registered: {obj.registration_date.strftime('%Y-%m-%d')})"


class EventNotificationForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Important Update: Event Schedule Change'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Compose your message here. HTML is allowed if your email sending utility supports it.'}),
        help_text="You can use basic HTML tags for formatting if your email sending setup allows."
    )