from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ProfessorNote, NoteComment


class ProfessorNoteForm(forms.ModelForm):
    class Meta:
        model = ProfessorNote
        fields = ['student', 'subject', 'note_type', 'score', 'max_score', 'coefficient', 'comment', 'private_note']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'note_type': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '100'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'private_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class NoteApprovalForm(forms.ModelForm):
    class Meta:
        model = ProfessorNote
        fields = ['status', 'approval_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('approved', _('Approve')),
                ('rejected', _('Reject')),
                ('revision_requested', _('Request Revision')),
            ]),
            'approval_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class NoteCommentForm(forms.ModelForm):
    class Meta:
        model = NoteComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Add a comment...')}),
        }
