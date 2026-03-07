"""
Initial/reference data for the Scheduling app.
Seeds: Rooms, TimeSlots.
Requires: tenant (School instance).
"""
from datetime import time


ROOMS_DATA = [
    {'name': 'Room 101', 'code': 'R101', 'building': 'Main Building', 'floor': 1, 'capacity': 40, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Room 102', 'code': 'R102', 'building': 'Main Building', 'floor': 1, 'capacity': 40, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Room 103', 'code': 'R103', 'building': 'Main Building', 'floor': 1, 'capacity': 35, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Room 201', 'code': 'R201', 'building': 'Main Building', 'floor': 2, 'capacity': 40, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Room 202', 'code': 'R202', 'building': 'Main Building', 'floor': 2, 'capacity': 40, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Room 301', 'code': 'R301', 'building': 'Main Building', 'floor': 3, 'capacity': 35, 'room_type': 'classroom', 'equipment': ['projector', 'whiteboard']},
    {'name': 'Computer Lab A', 'code': 'CLA', 'building': 'Science Building', 'floor': 1, 'capacity': 30, 'room_type': 'computer_room', 'equipment': ['computers', 'projector']},
    {'name': 'Computer Lab B', 'code': 'CLB', 'building': 'Science Building', 'floor': 1, 'capacity': 30, 'room_type': 'computer_room', 'equipment': ['computers', 'projector']},
    {'name': 'Physics Lab', 'code': 'PHL', 'building': 'Science Building', 'floor': 2, 'capacity': 25, 'room_type': 'lab', 'equipment': ['lab_equipment', 'projector']},
    {'name': 'Chemistry Lab', 'code': 'CHL', 'building': 'Science Building', 'floor': 2, 'capacity': 25, 'room_type': 'lab', 'equipment': ['lab_equipment', 'fume_hood']},
    {'name': 'Biology Lab', 'code': 'BIL', 'building': 'Science Building', 'floor': 3, 'capacity': 25, 'room_type': 'lab', 'equipment': ['microscopes', 'lab_equipment']},
    {'name': 'Amphitheatre A', 'code': 'AMA', 'building': 'Lecture Hall', 'floor': 0, 'capacity': 200, 'room_type': 'amphitheatre', 'equipment': ['projector', 'microphone', 'speakers']},
    {'name': 'Amphitheatre B', 'code': 'AMB', 'building': 'Lecture Hall', 'floor': 0, 'capacity': 150, 'room_type': 'amphitheatre', 'equipment': ['projector', 'microphone', 'speakers']},
    {'name': 'Meeting Room 1', 'code': 'MR1', 'building': 'Admin Building', 'floor': 1, 'capacity': 15, 'room_type': 'meeting', 'equipment': ['projector', 'whiteboard', 'video_conferencing']},
    {'name': 'Library Hall', 'code': 'LBH', 'building': 'Library', 'floor': 0, 'capacity': 80, 'room_type': 'classroom', 'equipment': ['projector']},
]

# (name, start_time, end_time, slot_type, order)
TIMESLOT_TEMPLATE = [
    ('Period 1', time(8, 0), time(9, 0), 'class', 1),
    ('Period 2', time(9, 0), time(10, 0), 'class', 2),
    ('Morning Break', time(10, 0), time(10, 15), 'break', 3),
    ('Period 3', time(10, 15), time(11, 15), 'class', 4),
    ('Period 4', time(11, 15), time(12, 15), 'class', 5),
    ('Lunch Break', time(12, 15), time(13, 15), 'lunch', 6),
    ('Period 5', time(13, 15), time(14, 15), 'class', 7),
    ('Period 6', time(14, 15), time(15, 15), 'class', 8),
    ('Afternoon Break', time(15, 15), time(15, 30), 'break', 9),
    ('Period 7', time(15, 30), time(16, 30), 'class', 10),
    ('Period 8', time(16, 30), time(17, 30), 'class', 11),
]

# Monday=0 through Friday=4
WEEKDAYS = [0, 1, 2, 3, 4]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed Rooms and TimeSlots. Requires tenant."""
    from .models import Room, TimeSlot

    if not tenant:
        if stdout:
            stdout.write('  [SKIP] Scheduling: No tenant provided (required for Rooms and TimeSlots)')
        return {'rooms': [], 'timeslots': []}

    results = {'rooms': [], 'timeslots': []}
    room_created = 0
    room_existed = 0
    slot_created = 0
    slot_existed = 0

    # Seed Rooms
    for data in ROOMS_DATA:
        obj, created = Room.objects.get_or_create(
            tenant=tenant,
            code=data['code'],
            defaults={
                'name': data['name'],
                'building': data['building'],
                'floor': data['floor'],
                'capacity': data['capacity'],
                'room_type': data['room_type'],
                'equipment': data['equipment'],
                'is_active': True,
            },
        )
        if created:
            room_created += 1
        else:
            room_existed += 1
        results['rooms'].append(obj)

    # Seed TimeSlots for each weekday
    for day in WEEKDAYS:
        for name, start, end, slot_type, order in TIMESLOT_TEMPLATE:
            obj, created = TimeSlot.objects.get_or_create(
                tenant=tenant,
                day_of_week=day,
                start_time=start,
                defaults={
                    'name': name,
                    'end_time': end,
                    'slot_type': slot_type,
                    'order': order,
                    'is_active': True,
                },
            )
            if created:
                slot_created += 1
            else:
                slot_existed += 1
            results['timeslots'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  Room: {room_created} created, {room_existed} already existed')
        stdout.write(f'  TimeSlot: {slot_created} created, {slot_existed} already existed')

    return results
