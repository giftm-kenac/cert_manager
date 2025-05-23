# Generated by Django 5.2 on 2025-05-19 17:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_skill_certificationtype_earning_criteria_and_more'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The official name of the event.', max_length=255)),
                ('description', models.TextField(help_text='A detailed description of the event.')),
                ('venue', models.CharField(help_text='Physical or virtual location of the event.', max_length=255)),
                ('date', models.DateField(help_text='Date of the event.')),
                ('time', models.TimeField(help_text='Start time of the event.')),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly identifier. Auto-generated if left blank.', max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Controls if public registration is open.')),
                ('max_attendees', models.PositiveIntegerField(blank=True, help_text='Maximum number of allowed registrations (optional).', null=True)),
                ('registration_deadline', models.DateTimeField(blank=True, help_text='Registrations close after this date/time (optional).', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('certification_type', models.ForeignKey(blank=True, help_text='Certificate to be awarded upon completion/attendance (optional).', null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.certificationtype')),
                ('created_by', models.ForeignKey(help_text='Employee who created this event.', limit_choices_to={'is_employee': True}, on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to='users.employeeprofile')),
            ],
            options={
                'ordering': ['-date', '-time'],
            },
        ),
        migrations.CreateModel(
            name='EventQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(help_text="The question text (e.g., 'Full Name & Surname').", max_length=500)),
                ('field_type', models.CharField(choices=[('text', 'Text (Single Line)'), ('email', 'Email'), ('phone', 'Phone Number'), ('textarea', 'Text Area (Multi-line)'), ('select', 'Dropdown Select'), ('radio', 'Radio Buttons (Single Choice)'), ('checkbox', 'Checkboxes (Multiple Choices Possible)'), ('number', 'Number'), ('date', 'Date')], help_text='The type of input field for this question.', max_length=20)),
                ('is_required', models.BooleanField(default=True, help_text='Is answering this question mandatory?')),
                ('order', models.PositiveIntegerField(default=0, help_text='Order in which questions appear on the form.')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='core.event')),
            ],
            options={
                'ordering': ['event', 'order'],
            },
        ),
        migrations.CreateModel(
            name='EventQuestionOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_text', models.CharField(help_text="The text displayed for this option (e.g., 'Small', 'Visit to the Falls').", max_length=255)),
                ('value', models.CharField(blank=True, help_text='The value stored if this option is selected (defaults to option_text if blank).', max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='core.eventquestion')),
            ],
            options={
                'ordering': ['question', 'option_text'],
            },
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
                ('attended', models.BooleanField(default=False, help_text='Marked by admin if the user attended the event.')),
                ('status', models.CharField(choices=[('REGISTERED', 'Registered'), ('CONFIRMED', 'Confirmed'), ('CANCELLED_BY_USER', 'Cancelled by User'), ('CANCELLED_BY_ADMIN', 'Cancelled by Admin'), ('WAITLISTED', 'Waitlisted'), ('ATTENDED', 'Attended'), ('NOT_ATTENDED', 'Not Attended')], default='REGISTERED', max_length=20)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='core.event')),
                ('user', models.ForeignKey(help_text='The client who registered.', on_delete=django.db.models.deletion.CASCADE, related_name='event_registrations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-registration_date'],
                'unique_together': {('event', 'user')},
            },
        ),
        migrations.CreateModel(
            name='EventRegistrationAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField(blank=True, help_text="The user's answer for text-based or single-choice questions.", null=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_answers', to='core.eventquestion')),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='core.eventregistration')),
                ('selected_options', models.ManyToManyField(blank=True, help_text='For checkbox questions, links to the selected options.', related_name='answer_selections', to='core.eventquestionoption')),
            ],
            options={
                'ordering': ['registration', 'question__order'],
                'unique_together': {('registration', 'question')},
            },
        ),
    ]
