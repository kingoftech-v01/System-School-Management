"""
Data collector for the scheduling engine.
Gathers all inputs needed before timetable generation.
"""

from django.contrib.auth import get_user_model

from .types import SchedulingUnit

User = get_user_model()


class ScheduleDataCollector:
    """Collects and prepares all data needed for timetable generation."""

    def __init__(self, tenant, session, semester, filiere_ids=None):
        self.tenant = tenant
        self.session = session
        self.semester = semester
        self.filiere_ids = filiere_ids

    def collect_scheduling_units(self):
        """Build list of SchedulingUnits from FiliereSubject + CourseAllocation."""
        from filieres.models import FiliereSubject
        from course.models import CourseAllocation

        subjects = FiliereSubject.objects.filter(
            filiere__tenant=self.tenant,
        ).select_related('filiere', 'subject')

        if self.filiere_ids:
            subjects = subjects.filter(filiere_id__in=self.filiere_ids)

        # Filter by semester name
        if self.semester:
            subjects = subjects.filter(semester=self.semester.semester)

        # Build allocation map: course_id -> professor
        allocations = CourseAllocation.objects.filter(
            session=self.session
        ).prefetch_related('courses')

        course_prof_map = {}
        for alloc in allocations:
            for course in alloc.courses.all():
                course_prof_map[course.id] = alloc.lecturer

        units = []
        for fs in subjects:
            professor = course_prof_map.get(fs.subject_id)
            if not professor:
                continue  # Skip unallocated courses

            hours = fs.hours_per_week or 2
            # Estimate slots needed (assuming 1 slot = 1-2 hours)
            slots_needed = max(1, hours // 2)

            # Check if course requires lab
            requires_lab = any(
                kw in (fs.subject.title or '').lower()
                for kw in ['lab', 'tp', 'pratique', 'practical']
            )

            # Estimate student count
            expected_students = self._get_student_count(fs.filiere, fs.year)

            unit = SchedulingUnit(
                id=f"{fs.filiere_id}_{fs.subject_id}_{fs.year}",
                course_id=fs.subject_id,
                course_title=fs.subject.title,
                course_code=fs.subject.code,
                professor_id=professor.id,
                professor_name=professor.get_full_name,
                filiere_id=fs.filiere_id,
                filiere_name=fs.filiere.name,
                year=fs.year,
                hours_per_week=hours,
                slots_needed=slots_needed,
                requires_lab=requires_lab,
                expected_students=expected_students,
            )
            units.append(unit)

        return units

    def collect_rooms(self):
        """Get all active rooms for the tenant."""
        from scheduling.models import Room
        return list(Room.objects.filter(tenant=self.tenant, is_active=True))

    def collect_time_slots(self):
        """Get all active class time slots for the tenant."""
        from scheduling.models import TimeSlot
        return list(TimeSlot.objects.filter(
            tenant=self.tenant, is_active=True, slot_type='class'
        ).order_by('day_of_week', 'order'))

    def collect_professor_availability(self):
        """Get professor availability preferences."""
        from scheduling.models import ProfessorAvailability
        prefs = ProfessorAvailability.objects.filter(
            time_slot__tenant=self.tenant,
        ).select_related('time_slot')

        availability = {}
        for pref in prefs:
            availability[(pref.professor_id, pref.time_slot_id)] = pref.preference

        return availability

    def collect_locked_entries(self):
        """Get entries that should not be moved during generation."""
        from scheduling.models import ScheduleEntry
        return list(ScheduleEntry.objects.filter(
            tenant=self.tenant,
            is_locked=True,
            status='active',
        ).select_related('time_slot'))

    def _get_student_count(self, filiere, year):
        """Estimate number of students in a filiere/year."""
        from accounts.models import Student
        try:
            return Student.objects.filter(
                program=filiere,
                level=str(year * 100) if year else None,
            ).count() or filiere.capacity or 30
        except Exception:
            return filiere.capacity if hasattr(filiere, 'capacity') else 30
