"""
Main timetable generator - orchestrates the scheduling algorithm.

Algorithm:
1. Collect data (scheduling units, rooms, time slots, availability)
2. Sort units by constraint score (most constrained first - MRV heuristic)
3. Greedy placement with constraint satisfaction
4. Local search optimization
5. Validation and conflict detection
"""

import logging
from collections import defaultdict
from datetime import date

from django.utils import timezone

from .collector import ScheduleDataCollector
from .scorer import SoftScorer
from .validator import detect_conflicts
from .local_search import LocalSearchOptimizer

logger = logging.getLogger(__name__)


class TimetableGenerator:
    """Generates a complete timetable for a semester."""

    def __init__(self, generation):
        """
        Args:
            generation: TimetableGeneration model instance with config
        """
        self.generation = generation
        self.tenant = generation.tenant
        self.session = generation.session
        self.semester = generation.semester
        self.config = generation.config or {}

    def generate(self):
        """Run the full generation pipeline."""
        from scheduling.models import ScheduleEntry

        self.generation.status = 'running'
        self.generation.started_at = timezone.now()
        self.generation.save(update_fields=['status', 'started_at'])

        try:
            # Phase 1: Collect data
            collector = ScheduleDataCollector(
                tenant=self.tenant,
                session=self.session,
                semester=self.semester,
                filiere_ids=self.config.get('filiere_ids'),
            )
            units = collector.collect_scheduling_units()
            rooms = collector.collect_rooms()
            time_slots = collector.collect_time_slots()
            availability = collector.collect_professor_availability()
            locked_entries = collector.collect_locked_entries()

            if not units:
                self._finish('completed', 0, 0, [{'type': 'warning', 'message': 'No courses to schedule'}])
                return
            if not rooms:
                self._finish('failed', 0, 0, [{'type': 'error', 'message': 'No rooms available'}])
                return
            if not time_slots:
                self._finish('failed', 0, 0, [{'type': 'error', 'message': 'No time slots configured'}])
                return

            # Phase 2: Calculate constraint scores and sort
            self._calculate_constraint_scores(units, rooms, time_slots, availability)
            units.sort(key=lambda u: u.constraint_score, reverse=True)

            # Phase 3: Initialize occupation matrices from locked entries
            prof_occupied = defaultdict(set)
            room_occupied = defaultdict(set)
            group_occupied = defaultdict(set)

            for entry in locked_entries:
                prof_occupied[entry.professor_id].add(entry.time_slot_id)
                if entry.room_id:
                    room_occupied[entry.room_id].add(entry.time_slot_id)
                if entry.filiere_id:
                    group_occupied[entry.filiere_id].add(entry.time_slot_id)

            # Phase 4: Greedy placement
            scorer = SoftScorer(availability, time_slots)
            created_entries = []
            unscheduled = []

            effective_from = date.fromisoformat(
                self.config.get('effective_from', date.today().isoformat())
            )
            effective_until = date.fromisoformat(
                self.config.get('effective_until', date.today().replace(
                    month=min(date.today().month + 4, 12)
                ).isoformat())
            )

            for unit in units:
                placed = 0
                used_days = set()

                for _ in range(unit.slots_needed):
                    best_slot = None
                    best_room = None
                    best_score = float('-inf')

                    for ts in time_slots:
                        # Prefer different days
                        if ts.day_of_week in used_days and best_slot is not None:
                            continue

                        # Hard constraint checks
                        if ts.id in prof_occupied[unit.professor_id]:
                            continue
                        group_key = unit.filiere_id
                        if ts.id in group_occupied[group_key]:
                            continue

                        # Find a valid room
                        valid_room = self._find_room(
                            unit, ts, rooms, room_occupied
                        )
                        if not valid_room:
                            continue

                        # Score this placement
                        score = scorer.score(unit, ts, valid_room, None)
                        if score > best_score:
                            best_score = score
                            best_slot = ts
                            best_room = valid_room

                    if best_slot and best_room:
                        # Create the entry
                        entry = ScheduleEntry.objects.create(
                            tenant=self.tenant,
                            course_id=unit.course_id,
                            professor_id=unit.professor_id,
                            room=best_room,
                            time_slot=best_slot,
                            filiere_id=unit.filiere_id,
                            session=self.session,
                            semester=self.semester,
                            effective_from=effective_from,
                            effective_until=effective_until,
                            recurrence='weekly',
                            status='active',
                            generation=self.generation,
                            created_by=self.generation.created_by,
                        )
                        created_entries.append(entry)

                        # Update occupation matrices
                        prof_occupied[unit.professor_id].add(best_slot.id)
                        room_occupied[best_room.id].add(best_slot.id)
                        group_occupied[group_key].add(best_slot.id)
                        used_days.add(best_slot.day_of_week)

                        scorer.record_assignment(unit, best_slot, best_room)
                        placed += 1
                    else:
                        break

                if placed < unit.slots_needed:
                    unscheduled.append({
                        'course': unit.course_title,
                        'filiere': unit.filiere_name,
                        'placed': placed,
                        'needed': unit.slots_needed,
                    })

            # Phase 5: Local search optimization
            optimizer = LocalSearchOptimizer(scorer, max_iterations=500)
            improvements = optimizer.optimize(created_entries, time_slots, rooms)

            # Save any slot changes from optimization
            for entry in created_entries:
                entry.save(update_fields=['time_slot', 'updated_at'])

            # Phase 6: Validate
            conflicts = detect_conflicts(self.tenant, self.generation)
            conflict_details = [
                {
                    'type': c.conflict_type,
                    'severity': c.severity,
                    'description': c.description,
                }
                for c in conflicts
            ]
            if unscheduled:
                for u in unscheduled:
                    conflict_details.append({
                        'type': 'unscheduled',
                        'severity': 'hard',
                        'description': (
                            f"Could not schedule {u['course']} for {u['filiere']} "
                            f"({u['placed']}/{u['needed']} slots placed)"
                        ),
                    })

            self._finish(
                'completed',
                len(created_entries),
                len(conflicts) + len(unscheduled),
                conflict_details,
            )

            logger.info(
                f"Timetable generation #{self.generation.id} completed: "
                f"{len(created_entries)} entries, {len(conflicts)} conflicts, "
                f"{improvements} optimizations"
            )

        except Exception as e:
            logger.exception(f"Timetable generation #{self.generation.id} failed")
            self._finish('failed', 0, 0, [{'type': 'error', 'message': str(e)}])
            raise

    def _calculate_constraint_scores(self, units, rooms, time_slots, availability):
        """Calculate how constrained each unit is (higher = more constrained)."""
        lab_rooms = [r for r in rooms if r.room_type in ('lab', 'computer_room')]

        for unit in units:
            score = 0.0

            # Fewer valid rooms = more constrained
            valid_rooms = [
                r for r in rooms
                if r.capacity >= unit.expected_students
                and (not unit.requires_lab or r.room_type in ('lab', 'computer_room'))
            ]
            score += 10.0 / max(len(valid_rooms), 1)

            # Professor availability constraints
            unavailable_count = sum(
                1 for ts in time_slots
                if availability.get((unit.professor_id, ts.id)) == 'unavailable'
            )
            available_slots = len(time_slots) - unavailable_count
            score += 10.0 / max(available_slots, 1)

            # More hours needed = more constrained
            score += unit.slots_needed * 2

            # Lab requirement = more constrained
            if unit.requires_lab:
                score += 5

            unit.constraint_score = score

    def _find_room(self, unit, time_slot, rooms, room_occupied):
        """Find a suitable room for the unit at the given time slot."""
        candidates = []
        for room in rooms:
            if time_slot.id in room_occupied[room.id]:
                continue
            if room.capacity < unit.expected_students:
                continue
            if unit.requires_lab and room.room_type not in ('lab', 'computer_room'):
                continue
            candidates.append(room)

        if not candidates:
            return None

        # Prefer smallest sufficient room (avoid wasting large rooms)
        candidates.sort(key=lambda r: r.capacity)
        return candidates[0]

    def _finish(self, status, entries_created, conflicts_found, conflict_details):
        """Update generation record with results."""
        self.generation.status = status
        self.generation.entries_created = entries_created
        self.generation.conflicts_found = conflicts_found
        self.generation.conflict_details = conflict_details
        self.generation.completed_at = timezone.now()
        self.generation.save()
