"""
Soft constraint scoring for the scheduling engine.
Evaluates how "good" a particular slot assignment is.
"""

from collections import defaultdict


class SoftScorer:
    """Calculates soft constraint scores for slot assignments."""

    def __init__(self, professor_availability, time_slots):
        self.professor_availability = professor_availability
        self.time_slots = {ts.id: ts for ts in time_slots}

        # Track assignments for gap/distribution scoring
        self.professor_day_slots = defaultdict(lambda: defaultdict(list))
        self.group_day_slots = defaultdict(lambda: defaultdict(list))
        self.course_rooms = defaultdict(set)

    def score(self, unit, time_slot, room, assignments_state):
        """Calculate soft score for placing a unit at a given slot/room.

        Higher score = better assignment.
        """
        score = 0.0

        # 1. Professor preference (weight: 20)
        pref = self.professor_availability.get(
            (unit.professor_id, time_slot.id), 'neutral'
        )
        if pref == 'preferred':
            score += 20
        elif pref == 'neutral':
            score += 10
        elif pref == 'avoid':
            score -= 15
        elif pref == 'unavailable':
            score -= 1000  # Effectively a hard constraint

        # 2. Morning preference for heavy courses (weight: 10)
        if unit.hours_per_week >= 4 and time_slot.order <= 2:
            score += 10

        # 3. Room consistency (weight: 15)
        existing_rooms = self.course_rooms.get(unit.course_id, set())
        if room.id in existing_rooms:
            score += 15
        elif not existing_rooms:
            score += 5  # First assignment, neutral

        # 4. Minimize gaps for student group (weight: 25)
        group_key = (unit.filiere_id, unit.year)
        existing_slots = self.group_day_slots[group_key][time_slot.day_of_week]
        if existing_slots:
            orders = sorted([s.order for s in existing_slots] + [time_slot.order])
            gaps = sum(1 for i in range(len(orders) - 1) if orders[i + 1] - orders[i] > 1)
            score -= gaps * 5

        # 5. Even distribution across week (weight: 15)
        group_day_counts = {
            day: len(slots)
            for day, slots in self.group_day_slots[group_key].items()
        }
        current_count = group_day_counts.get(time_slot.day_of_week, 0) + 1
        avg_count = (sum(group_day_counts.values()) + 1) / max(len(group_day_counts) + 1, 1)
        deviation = abs(current_count - avg_count)
        score -= deviation * 3

        # 6. Professor workload distribution (weight: 10)
        prof_day_counts = {
            day: len(slots)
            for day, slots in self.professor_day_slots[unit.professor_id].items()
        }
        prof_current = prof_day_counts.get(time_slot.day_of_week, 0) + 1
        prof_avg = (sum(prof_day_counts.values()) + 1) / max(len(prof_day_counts) + 1, 1)
        score -= abs(prof_current - prof_avg) * 2

        return score

    def record_assignment(self, unit, time_slot, room):
        """Update internal tracking after an assignment is made."""
        self.professor_day_slots[unit.professor_id][time_slot.day_of_week].append(time_slot)
        group_key = (unit.filiere_id, unit.year)
        self.group_day_slots[group_key][time_slot.day_of_week].append(time_slot)
        self.course_rooms[unit.course_id].add(room.id)
