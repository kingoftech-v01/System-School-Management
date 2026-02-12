"""
Management command to create default rooms and time slots for a school.
Usage: python manage.py seed_rooms_and_slots --settings=School_System.settings.development
"""

from django.core.management.base import BaseCommand
from django.conf import settings

from core.models import School
from scheduling.models import Room, TimeSlot


DEFAULT_ROOMS = [
    {'name': 'Salle 101', 'code': 'S101', 'building': 'Batiment A', 'floor': 1, 'capacity': 40, 'room_type': 'classroom'},
    {'name': 'Salle 102', 'code': 'S102', 'building': 'Batiment A', 'floor': 1, 'capacity': 40, 'room_type': 'classroom'},
    {'name': 'Salle 103', 'code': 'S103', 'building': 'Batiment A', 'floor': 1, 'capacity': 30, 'room_type': 'classroom'},
    {'name': 'Salle 201', 'code': 'S201', 'building': 'Batiment A', 'floor': 2, 'capacity': 35, 'room_type': 'classroom'},
    {'name': 'Salle 202', 'code': 'S202', 'building': 'Batiment A', 'floor': 2, 'capacity': 35, 'room_type': 'classroom'},
    {'name': 'Amphitheatre A', 'code': 'AMP-A', 'building': 'Batiment B', 'floor': 0, 'capacity': 150, 'room_type': 'amphitheatre'},
    {'name': 'Amphitheatre B', 'code': 'AMP-B', 'building': 'Batiment B', 'floor': 0, 'capacity': 100, 'room_type': 'amphitheatre'},
    {'name': 'Labo Informatique 1', 'code': 'LAB-I1', 'building': 'Batiment C', 'floor': 1, 'capacity': 25, 'room_type': 'computer_room', 'equipment': ['computers', 'projector']},
    {'name': 'Labo Informatique 2', 'code': 'LAB-I2', 'building': 'Batiment C', 'floor': 1, 'capacity': 25, 'room_type': 'computer_room', 'equipment': ['computers', 'projector']},
    {'name': 'Laboratoire Sciences', 'code': 'LAB-S', 'building': 'Batiment C', 'floor': 2, 'capacity': 20, 'room_type': 'lab', 'equipment': ['science_equipment', 'projector']},
    {'name': 'Salle de Reunion', 'code': 'REU-1', 'building': 'Batiment A', 'floor': 0, 'capacity': 15, 'room_type': 'meeting'},
]

# Time slots for Mon-Sat, typical school schedule
DEFAULT_SLOTS = [
    # Each tuple: (name, start, end, slot_type, order)
    ('08h00-10h00', '08:00', '10:00', 'class', 1),
    ('10h00-10h15', '10:00', '10:15', 'break', 2),
    ('10h15-12h15', '10:15', '12:15', 'class', 3),
    ('12h15-13h30', '12:15', '13:30', 'lunch', 4),
    ('13h30-15h30', '13:30', '15:30', 'class', 5),
    ('15h30-15h45', '15:30', '15:45', 'break', 6),
    ('15h45-17h45', '15:45', '17:45', 'class', 7),
]


class Command(BaseCommand):
    help = 'Create default rooms and time slots for a school'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant', type=str, default='default',
            help='School slug (default: "default")'
        )

    def handle(self, *args, **options):
        slug = options['tenant']
        try:
            school = School.objects.get(slug=slug)
        except School.DoesNotExist:
            school, _ = School.objects.get_or_create(
                slug='default',
                defaults={'name': 'Default School', 'email': 'admin@school.local'}
            )

        self.stdout.write(f"Seeding rooms and time slots for: {school.name}")

        # Create rooms
        rooms_created = 0
        for room_data in DEFAULT_ROOMS:
            equipment = room_data.pop('equipment', [])
            _, created = Room.objects.get_or_create(
                tenant=school,
                code=room_data['code'],
                defaults={**room_data, 'equipment': equipment},
            )
            if created:
                rooms_created += 1

        self.stdout.write(self.style.SUCCESS(f"  Rooms: {rooms_created} created"))

        # Create time slots for Mon-Sat (days 0-5)
        slots_created = 0
        for day in range(6):  # Monday to Saturday
            for name, start, end, slot_type, order in DEFAULT_SLOTS:
                _, created = TimeSlot.objects.get_or_create(
                    tenant=school,
                    day_of_week=day,
                    start_time=start,
                    defaults={
                        'name': name,
                        'end_time': end,
                        'slot_type': slot_type,
                        'order': order,
                    },
                )
                if created:
                    slots_created += 1

        self.stdout.write(self.style.SUCCESS(f"  Time slots: {slots_created} created"))
        self.stdout.write(self.style.SUCCESS("Done!"))
