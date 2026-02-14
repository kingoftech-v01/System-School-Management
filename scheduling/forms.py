from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div, Field

from .models import (
    Room, TimeSlot, ScheduleEntry, ScheduleException,
    SubstitutionRequest, ProfessorAvailability,
    DAY_OF_WEEK_CHOICES, ROOM_TYPE_CHOICES, SLOT_TYPE_CHOICES,
)


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'name', 'code', 'building', 'floor', 'capacity',
            'room_type', 'equipment', 'is_active',
        ]
        widgets = {
            'equipment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '["projector", "whiteboard", "computers"]',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('code', css_class='col-md-6'),
            ),
            Row(
                Column('building', css_class='col-md-4'),
                Column('floor', css_class='col-md-4'),
                Column('capacity', css_class='col-md-4'),
            ),
            Row(
                Column('room_type', css_class='col-md-6'),
                Column('is_active', css_class='col-md-6 mt-4'),
            ),
            'equipment',
            Submit('submit', _('Save Room'), css_class='btn btn-primary'),
        )


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = [
            'name', 'day_of_week', 'start_time', 'end_time',
            'slot_type', 'order', 'is_active',
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('day_of_week', css_class='col-md-6'),
            ),
            Row(
                Column('start_time', css_class='col-md-4'),
                Column('end_time', css_class='col-md-4'),
                Column('slot_type', css_class='col-md-4'),
            ),
            Row(
                Column('order', css_class='col-md-6'),
                Column('is_active', css_class='col-md-6 mt-4'),
            ),
            Submit('submit', _('Save Time Slot'), css_class='btn btn-primary'),
        )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError(_('End time must be after start time.'))
        return cleaned


class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
        fields = [
            'course', 'professor', 'room', 'time_slot', 'filiere',
            'group_name', 'session', 'semester', 'effective_from',
            'effective_until', 'recurrence', 'status', 'color', 'is_locked',
        ]
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_until': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('course', css_class='col-md-6'),
                Column('professor', css_class='col-md-6'),
            ),
            Row(
                Column('room', css_class='col-md-4'),
                Column('time_slot', css_class='col-md-4'),
                Column('filiere', css_class='col-md-4'),
            ),
            Row(
                Column('group_name', css_class='col-md-4'),
                Column('session', css_class='col-md-4'),
                Column('semester', css_class='col-md-4'),
            ),
            Row(
                Column('effective_from', css_class='col-md-4'),
                Column('effective_until', css_class='col-md-4'),
                Column('recurrence', css_class='col-md-4'),
            ),
            Row(
                Column('status', css_class='col-md-4'),
                Column('color', css_class='col-md-4'),
                Column('is_locked', css_class='col-md-4 mt-4'),
            ),
            Submit('submit', _('Save Schedule Entry'), css_class='btn btn-primary'),
        )

        # Filter querysets by tenant if provided
        if tenant:
            self.fields['room'].queryset = Room.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields['time_slot'].queryset = TimeSlot.objects.filter(
                tenant=tenant, is_active=True
            )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('effective_from')
        end = cleaned.get('effective_until')
        if start and end and end < start:
            raise forms.ValidationError(_('Effective until must be after effective from.'))
        return cleaned


class ScheduleExceptionForm(forms.ModelForm):
    class Meta:
        model = ScheduleException
        fields = [
            'schedule_entry', 'exception_type', 'date',
            'new_room', 'substitute_professor',
            'new_start_time', 'new_end_time',
            'reason', 'notify_students',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'new_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'new_end_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('schedule_entry', css_class='col-md-6'),
                Column('exception_type', css_class='col-md-6'),
            ),
            Row(
                Column('date', css_class='col-md-4'),
                Column('new_room', css_class='col-md-4'),
                Column('substitute_professor', css_class='col-md-4'),
            ),
            Row(
                Column('new_start_time', css_class='col-md-6'),
                Column('new_end_time', css_class='col-md-6'),
            ),
            'reason',
            'notify_students',
            Submit('submit', _('Save Exception'), css_class='btn btn-primary'),
        )


class SubstitutionRequestForm(forms.ModelForm):
    class Meta:
        model = SubstitutionRequest
        fields = ['schedule_entry', 'date', 'suggested_substitute', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('schedule_entry', css_class='col-md-6'),
                Column('date', css_class='col-md-6'),
            ),
            'suggested_substitute',
            'reason',
            Submit('submit', _('Submit Request'), css_class='btn btn-primary'),
        )


class CancellationForm(forms.Form):
    """Simple form for professors to cancel a class on a specific date."""
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    notify_students = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'date',
            'reason',
            'notify_students',
            Submit('submit', _('Cancel Class'), css_class='btn btn-danger'),
        )
