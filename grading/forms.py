"""
Grading Forms - Django forms for grading management.

This module provides forms for:
- Creating and editing grading rubrics
- Managing rubric criteria
- Entering grades
- Submitting peer reviews
- Applying grade curves
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import formset_factory, BaseFormSet
from decimal import Decimal

from .models import (
    GradingRubric, RubricCriterion, RubricGrade, CriterionGrade,
    PeerReview, GradeCurve
)
from course.models import Course
from accounts.models import Student


class GradingRubricForm(forms.ModelForm):
    """Form for creating/editing grading rubrics."""

    class Meta:
        model = GradingRubric
        fields = ['name', 'description', 'course', 'max_score', 'passing_score',
                  'is_active', 'allow_partial_credit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_partial_credit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter courses based on user role
        if self.user:
            if self.user.role == 'lecturer':
                self.fields['course'].queryset = Course.objects.filter(
                    allocated_course__lecturer=self.user
                ).distinct()
            elif self.user.role == 'direction':
                self.fields['course'].queryset = Course.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        max_score = cleaned_data.get('max_score')
        passing_score = cleaned_data.get('passing_score')

        if max_score and passing_score:
            if passing_score > max_score:
                raise forms.ValidationError(
                    _('Passing score cannot exceed maximum score.')
                )

        return cleaned_data


class RubricCriterionForm(forms.ModelForm):
    """Form for creating/editing rubric criteria."""

    class Meta:
        model = RubricCriterion
        fields = ['name', 'description', 'weight', 'max_points', 'order',
                  'excellent_description', 'good_description',
                  'satisfactory_description', 'needs_improvement_description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'excellent_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'good_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'satisfactory_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'needs_improvement_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight < 0 or weight > 100:
            raise forms.ValidationError(_('Weight must be between 0 and 100.'))
        return weight


class RubricGradeForm(forms.ModelForm):
    """Form for entering rubric grades."""

    class Meta:
        model = RubricGrade
        fields = ['student', 'rubric', 'assignment_name', 'assignment_type', 'overall_feedback']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'rubric': forms.Select(attrs={'class': 'form-select'}),
            'assignment_name': forms.TextInput(attrs={'class': 'form-control'}),
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'overall_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.rubric = kwargs.pop('rubric', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter students based on user's courses
        if self.user and self.user.role == 'lecturer':
            from course.models import CourseAllocation
            course_ids = CourseAllocation.objects.filter(
                lecturer=self.user
            ).values_list('courses__id', flat=True)
            self.fields['student'].queryset = Student.objects.filter(
                group__courses__id__in=course_ids
            ).distinct()

        # Pre-select rubric if provided
        if self.rubric:
            self.fields['rubric'].initial = self.rubric
            self.fields['rubric'].widget = forms.HiddenInput()


class CriterionGradeForm(forms.ModelForm):
    """Form for entering criterion grade."""

    class Meta:
        model = CriterionGrade
        fields = ['criterion', 'score', 'feedback']
        widgets = {
            'criterion': forms.HiddenInput(),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.criterion = kwargs.pop('criterion', None)
        super().__init__(*args, **kwargs)

        if self.criterion:
            self.fields['criterion'].initial = self.criterion
            self.fields['score'].widget.attrs['max'] = str(self.criterion.max_points)
            self.fields['score'].label = f"{self.criterion.name} (Max: {self.criterion.max_points})"

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if self.criterion and score > self.criterion.max_points:
            raise forms.ValidationError(
                _('Score cannot exceed maximum points for this criterion.')
            )
        return score


class BaseCriterionGradeFormSet(BaseFormSet):
    """Base formset for criterion grades."""

    def __init__(self, *args, **kwargs):
        self.rubric = kwargs.pop('rubric', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        """Override to pass criterion to each form."""
        if self.rubric:
            criteria = list(self.rubric.criteria.all().order_by('order'))
            if i < len(criteria):
                kwargs['criterion'] = criteria[i]
        return super()._construct_form(i, **kwargs)


# Create formset for criterion grades
CriterionGradeFormSet = formset_factory(
    CriterionGradeForm,
    formset=BaseCriterionGradeFormSet,
    extra=0,
    can_delete=False
)


class PeerReviewForm(forms.ModelForm):
    """Form for submitting peer reviews."""

    class Meta:
        model = PeerReview
        fields = ['score', 'feedback']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score < 0 or score > 100:
            raise forms.ValidationError(_('Score must be between 0 and 100.'))
        return score


class GradeCurveForm(forms.ModelForm):
    """Form for applying grade curves."""

    class Meta:
        model = GradeCurve
        fields = ['course', 'assignment_name', 'curve_type', 'adjustment_factor', 'add_points']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'assignment_name': forms.TextInput(attrs={'class': 'form-control'}),
            'curve_type': forms.Select(attrs={'class': 'form-select'}),
            'adjustment_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'add_points': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_adjustment_factor(self):
        adjustment_factor = self.cleaned_data.get('adjustment_factor')
        if adjustment_factor <= 0:
            raise forms.ValidationError(_('Adjustment factor must be greater than 0.'))
        return adjustment_factor
