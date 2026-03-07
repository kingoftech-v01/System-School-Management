"""Demo data generator for audit app: FieldChangeRecords."""

import random
import uuid
from django.contrib.contenttypes.models import ContentType

from .models import FieldChangeRecord


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    all_changers = professors + staff

    # Get ContentType for User model
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_ct = ContentType.objects.get_for_model(User)

    # Sample field changes for auditing
    field_changes = [
        ('first_name', 'First Name', 'John', 'Jonathan', 'update'),
        ('last_name', 'Last Name', 'Smith', 'Johnson', 'update'),
        ('email', 'Email', 'old@school.edu', 'new@school.edu', 'update'),
        ('phone', 'Phone', '+1234567890', '+0987654321', 'update'),
        ('role', 'Role', 'student', 'professor', 'update'),
        ('is_student', 'Is Student', 'True', 'False', 'update'),
        ('street_address', 'Street Address', '123 Old St', '456 New Ave', 'update'),
        ('city', 'City', 'Old City', 'New City', 'update'),
        ('gender', 'Gender', 'M', 'F', 'update'),
        ('date_of_birth', 'Date of Birth', '1990-01-01', '1991-02-15', 'update'),
    ]

    records = []
    student_users = [s.student for s in students[:30]]

    for i in range(50):
        user = random.choice(student_users)
        field_name, verbose_name, old_val, new_val, action = random.choice(field_changes)
        batch = uuid.uuid4()

        r = FieldChangeRecord.objects.create(
            content_type=user_ct,
            object_id=user.pk,
            field_name=field_name,
            field_verbose_name=verbose_name,
            old_value=old_val if action != 'create' else None,
            new_value=new_val if action != 'delete' else None,
            changed_by=random.choice(all_changers),
            change_reason=random.choice([
                'Profile update', 'Data correction', 'Administrative change',
                'User request', 'System migration', '',
            ]),
            batch_id=batch,
            action=action,
        )
        records.append(r)
    total += len(records)

    if stdout and verbosity >= 1:
        stdout.write(f'  [audit] Created {total} records')

    return {'_total': total}
