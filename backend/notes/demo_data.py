"""Demo data generator for notes app: ProfessorNote, NoteHistory, NoteComment."""

import random
from decimal import Decimal

from core.models import Session, Semester
from filieres.models import Filiere
from .models import ProfessorNote, NoteHistory, NoteComment


NOTE_TYPES = [
    'participation', 'homework', 'quiz', 'midterm', 'final',
    'project', 'presentation', 'behavior', 'attendance', 'other',
]

STATUSES = ['draft', 'pending', 'approved', 'rejected', 'revision_requested']

HISTORY_ACTIONS = [
    'created', 'updated', 'submitted', 'approved', 'rejected', 'revision_requested',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    session = context.get('session')
    semester = context.get('semester')
    total = 0

    filieres = list(Filiere.objects.all())
    if not filieres or not courses:
        if stdout:
            stdout.write('  [notes] No filieres or courses found, skipping')
        return {'_total': 0}

    # 1. Professor notes (300)
    notes = []
    for i in range(300):
        student = random.choice(students)
        professor = random.choice(professors)
        course = random.choice(courses)
        filiere = random.choice(filieres)
        status = random.choice(STATUSES)
        score = Decimal(str(round(random.uniform(20, 100), 2)))
        max_score = Decimal('100.00')
        coeff = Decimal(str(round(random.uniform(1.0, 5.0), 2)))

        note = ProfessorNote.objects.create(
            tenant=tenant,
            student=student.student,  # User FK, not Student FK
            professor=professor,
            filiere=filiere,
            subject=course,
            session=session,
            semester=semester,
            note_type=random.choice(NOTE_TYPES),
            score=score,
            max_score=max_score,
            coefficient=coeff,
            comment=fake.sentence() if random.random() < 0.6 else '',
            private_note=fake.sentence() if random.random() < 0.2 else '',
            status=status,
            submitted_for_approval=status != 'draft',
            approved_by=random.choice(professors) if status == 'approved' else None,
            approval_notes=fake.sentence() if status in ('approved', 'rejected', 'revision_requested') else '',
        )
        notes.append(note)
    total += len(notes)

    # 2. Note history (1 per note)
    history = []
    for note in notes:
        h = NoteHistory.objects.create(
            note=note,
            action='created',
            changed_by=note.professor,
            old_values={},
            new_values={'score': str(note.score), 'status': note.status},
            change_summary=f'Note created with score {note.score}',
        )
        history.append(h)

        # Add a second history entry for non-draft notes
        if note.status != 'draft':
            h2 = NoteHistory.objects.create(
                note=note,
                action='submitted',
                changed_by=note.professor,
                old_values={'status': 'draft'},
                new_values={'status': note.status},
                change_summary=f'Status changed to {note.status}',
            )
            history.append(h2)
    total += len(history)

    # 3. Note comments (50)
    comments = []
    for i in range(50):
        note = random.choice(notes)
        nc = NoteComment.objects.create(
            note=note,
            author=random.choice(professors + context['accounts']['staff_users'][:3]),
            comment=fake.paragraph(nb_sentences=2),
        )
        comments.append(nc)
    total += len(comments)

    if stdout and verbosity >= 1:
        stdout.write(f'  [notes] Created {total} records '
                     f'(notes: {len(notes)}, history: {len(history)}, comments: {len(comments)})')

    return {'_total': total}
