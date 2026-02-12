"""
Conflict detection and validation for the scheduling engine.
"""

from collections import defaultdict
from .types import ConflictInfo


def detect_conflicts(tenant, generation=None):
    """Detect all scheduling conflicts for a tenant's active entries.

    Returns a list of ConflictInfo objects.
    """
    from scheduling.models import ScheduleEntry

    entries = ScheduleEntry.objects.filter(
        tenant=tenant,
        status='active',
    ).select_related('course', 'professor', 'room', 'time_slot', 'filiere')

    if generation:
        entries = entries.filter(generation=generation)

    conflicts = []

    # Index entries by (day_of_week, time_slot_id)
    by_slot = defaultdict(list)
    for entry in entries:
        key = (entry.time_slot.day_of_week, entry.time_slot_id)
        by_slot[key].append(entry)

    for (day, slot_id), slot_entries in by_slot.items():
        # Professor overlap
        by_prof = defaultdict(list)
        for e in slot_entries:
            by_prof[e.professor_id].append(e)
        for prof_id, prof_entries in by_prof.items():
            if len(prof_entries) > 1:
                conflicts.append(ConflictInfo(
                    conflict_type='professor_overlap',
                    severity='hard',
                    description=(
                        f"Professor {prof_entries[0].professor.get_full_name} "
                        f"is double-booked at {prof_entries[0].time_slot}: "
                        f"{', '.join(e.course.title for e in prof_entries)}"
                    ),
                    entry_1_id=prof_entries[0].id,
                    entry_2_id=prof_entries[1].id,
                ))

        # Room overlap
        by_room = defaultdict(list)
        for e in slot_entries:
            if e.room_id:
                by_room[e.room_id].append(e)
        for room_id, room_entries in by_room.items():
            if len(room_entries) > 1:
                conflicts.append(ConflictInfo(
                    conflict_type='room_overlap',
                    severity='hard',
                    description=(
                        f"Room {room_entries[0].room.name} is double-booked at "
                        f"{room_entries[0].time_slot}: "
                        f"{', '.join(e.course.title for e in room_entries)}"
                    ),
                    entry_1_id=room_entries[0].id,
                    entry_2_id=room_entries[1].id,
                ))

        # Student group overlap
        by_group = defaultdict(list)
        for e in slot_entries:
            if e.filiere_id:
                by_group[e.filiere_id].append(e)
        for filiere_id, group_entries in by_group.items():
            if len(group_entries) > 1:
                # Check if they're for different groups
                groups = set(e.group_name for e in group_entries)
                if len(groups) <= 1 or '' in groups:
                    conflicts.append(ConflictInfo(
                        conflict_type='student_overlap',
                        severity='hard',
                        description=(
                            f"Students in {group_entries[0].filiere.name} have "
                            f"overlapping classes at {group_entries[0].time_slot}: "
                            f"{', '.join(e.course.title for e in group_entries)}"
                        ),
                        entry_1_id=group_entries[0].id,
                        entry_2_id=group_entries[1].id,
                    ))

    # Room capacity check
    for entry in entries:
        if entry.room and entry.filiere:
            expected = entry.filiere.capacity if hasattr(entry.filiere, 'capacity') else 30
            if expected > entry.room.capacity:
                conflicts.append(ConflictInfo(
                    conflict_type='room_capacity',
                    severity='soft',
                    description=(
                        f"Room {entry.room.name} (capacity {entry.room.capacity}) "
                        f"may be too small for {entry.course.title} "
                        f"({expected} expected students)"
                    ),
                    entry_1_id=entry.id,
                ))

    return conflicts
