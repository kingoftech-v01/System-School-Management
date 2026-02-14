"""
Initial/reference data for the Payments app.
Seeds: FeeStructures.
Requires: Programs from course/seed_data.
"""
from decimal import Decimal


# (program_title, level, academic_year, tuition, registration, library, lab, sports, other)
FEE_STRUCTURES_DATA = [
    ('Computer Science', 'bachelor', '2025-2026', Decimal('2500.00'), Decimal('150.00'), Decimal('75.00'), Decimal('200.00'), Decimal('50.00'), Decimal('75.00')),
    ('Business Administration', 'bachelor', '2025-2026', Decimal('2200.00'), Decimal('150.00'), Decimal('75.00'), Decimal('0.00'), Decimal('50.00'), Decimal('75.00')),
    ('Mechanical Engineering', 'bachelor', '2025-2026', Decimal('3000.00'), Decimal('200.00'), Decimal('75.00'), Decimal('300.00'), Decimal('50.00'), Decimal('100.00')),
    ('Electrical Engineering', 'bachelor', '2025-2026', Decimal('3000.00'), Decimal('200.00'), Decimal('75.00'), Decimal('300.00'), Decimal('50.00'), Decimal('100.00')),
    ('Civil Engineering', 'bachelor', '2025-2026', Decimal('2800.00'), Decimal('200.00'), Decimal('75.00'), Decimal('250.00'), Decimal('50.00'), Decimal('100.00')),
    ('Medicine', 'bachelor', '2025-2026', Decimal('5000.00'), Decimal('250.00'), Decimal('100.00'), Decimal('300.00'), Decimal('50.00'), Decimal('100.00')),
    ('Law', 'bachelor', '2025-2026', Decimal('2500.00'), Decimal('150.00'), Decimal('100.00'), Decimal('0.00'), Decimal('50.00'), Decimal('75.00')),
    ('Mathematics', 'bachelor', '2025-2026', Decimal('1800.00'), Decimal('125.00'), Decimal('75.00'), Decimal('0.00'), Decimal('50.00'), Decimal('50.00')),
    ('Physics', 'bachelor', '2025-2026', Decimal('2000.00'), Decimal('125.00'), Decimal('75.00'), Decimal('200.00'), Decimal('50.00'), Decimal('75.00')),
    ('Chemistry', 'bachelor', '2025-2026', Decimal('2000.00'), Decimal('125.00'), Decimal('75.00'), Decimal('250.00'), Decimal('50.00'), Decimal('75.00')),
    ('Biology', 'bachelor', '2025-2026', Decimal('2000.00'), Decimal('125.00'), Decimal('75.00'), Decimal('200.00'), Decimal('50.00'), Decimal('75.00')),
    ('Economics', 'bachelor', '2025-2026', Decimal('2000.00'), Decimal('125.00'), Decimal('75.00'), Decimal('0.00'), Decimal('50.00'), Decimal('50.00')),
    ('Psychology', 'bachelor', '2025-2026', Decimal('2000.00'), Decimal('125.00'), Decimal('75.00'), Decimal('100.00'), Decimal('50.00'), Decimal('75.00')),
    ('Education', 'bachelor', '2025-2026', Decimal('1500.00'), Decimal('100.00'), Decimal('75.00'), Decimal('0.00'), Decimal('50.00'), Decimal('50.00')),
    ('Literature', 'bachelor', '2025-2026', Decimal('1500.00'), Decimal('100.00'), Decimal('75.00'), Decimal('0.00'), Decimal('50.00'), Decimal('50.00')),
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed FeeStructures. Requires programs from context."""
    from .models import FeeStructure
    from course.models import Program

    results = {'fee_structures': []}
    created_count = 0
    existed_count = 0

    # Build program lookup
    program_map = {}
    for prog in Program.objects.all():
        program_map[prog.title] = prog

    for prog_title, level, year, tuition, reg, lib, lab, sports, other in FEE_STRUCTURES_DATA:
        program = program_map.get(prog_title)
        if not program:
            continue
        obj, created = FeeStructure.objects.get_or_create(
            program=program,
            level=level,
            academic_year=year,
            defaults={
                'tuition_fee': tuition,
                'registration_fee': reg,
                'library_fee': lib,
                'lab_fee': lab,
                'sports_fee': sports,
                'other_fees': other,
                'is_active': True,
            },
        )
        if created:
            created_count += 1
        else:
            existed_count += 1
        results['fee_structures'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  FeeStructure: {created_count} created, {existed_count} already existed')

    return results
