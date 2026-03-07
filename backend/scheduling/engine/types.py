"""Dataclasses for the scheduling engine."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SchedulingUnit:
    """Represents a course-section that needs to be scheduled."""
    id: str
    course_id: int
    course_title: str
    course_code: str
    professor_id: int
    professor_name: str
    filiere_id: int
    filiere_name: str
    year: int
    hours_per_week: int
    slots_needed: int
    requires_lab: bool
    expected_students: int
    constraint_score: float = 0.0


@dataclass
class SlotAssignment:
    """Represents a proposed assignment of a unit to a time/room."""
    unit: SchedulingUnit
    day_of_week: int
    time_slot_id: int
    room_id: int
    start_time: str
    end_time: str
    soft_score: float = 0.0


@dataclass
class ConflictInfo:
    """Represents a detected scheduling conflict."""
    conflict_type: str  # professor_overlap, room_overlap, student_overlap, room_capacity, etc.
    severity: str  # hard, soft
    description: str
    entry_1_id: Optional[int] = None
    entry_2_id: Optional[int] = None
