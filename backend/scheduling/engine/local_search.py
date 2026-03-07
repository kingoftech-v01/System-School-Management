"""
Local search / hill-climbing optimization for timetable improvement.
"""

import random
from collections import defaultdict


class LocalSearchOptimizer:
    """Improves timetable quality by swapping/moving entries."""

    def __init__(self, scorer, max_iterations=1000):
        self.scorer = scorer
        self.max_iterations = max_iterations

    def optimize(self, entries, time_slots, rooms):
        """Run hill-climbing optimization on the given entries.

        Tries to improve soft constraint scores by swapping time slots
        between compatible entries.

        Returns the number of improvements made.
        """
        improvements = 0
        iteration = 0

        # Index slots by day
        slots_by_day = defaultdict(list)
        for ts in time_slots:
            slots_by_day[ts.day_of_week].append(ts)

        # Build occupation maps
        prof_occupied = defaultdict(set)  # prof_id -> set of slot_ids
        room_occupied = defaultdict(set)  # room_id -> set of slot_ids
        group_occupied = defaultdict(set)  # (filiere_id, year) -> set of slot_ids

        for entry in entries:
            prof_occupied[entry.professor_id].add(entry.time_slot_id)
            if entry.room_id:
                room_occupied[entry.room_id].add(entry.time_slot_id)
            if entry.filiere_id:
                group_key = (entry.filiere_id, getattr(entry, '_year', 0))
                group_occupied[group_key].add(entry.time_slot_id)

        entry_list = [e for e in entries if not e.is_locked]
        if not entry_list:
            return 0

        while iteration < self.max_iterations:
            iteration += 1
            improved_this_round = False

            random.shuffle(entry_list)
            for entry in entry_list:
                # Try moving to a different slot
                current_slot = entry.time_slot
                best_score = 0  # Current assumed baseline
                best_slot = None

                for alt_slot in time_slots:
                    if alt_slot.id == current_slot.id:
                        continue

                    # Check hard constraints
                    if alt_slot.id in prof_occupied[entry.professor_id]:
                        continue
                    if entry.room_id and alt_slot.id in room_occupied[entry.room_id]:
                        continue
                    if entry.filiere_id:
                        group_key = (entry.filiere_id, getattr(entry, '_year', 0))
                        if alt_slot.id in group_occupied[group_key]:
                            continue

                    # Score improvement (simplified)
                    score_diff = self._estimate_improvement(entry, alt_slot)
                    if score_diff > best_score:
                        best_score = score_diff
                        best_slot = alt_slot

                if best_slot:
                    # Perform the move
                    old_slot = entry.time_slot
                    prof_occupied[entry.professor_id].discard(old_slot.id)
                    if entry.room_id:
                        room_occupied[entry.room_id].discard(old_slot.id)
                    if entry.filiere_id:
                        group_key = (entry.filiere_id, getattr(entry, '_year', 0))
                        group_occupied[group_key].discard(old_slot.id)

                    entry.time_slot = best_slot
                    entry.time_slot_id = best_slot.id

                    prof_occupied[entry.professor_id].add(best_slot.id)
                    if entry.room_id:
                        room_occupied[entry.room_id].add(best_slot.id)
                    if entry.filiere_id:
                        group_key = (entry.filiere_id, getattr(entry, '_year', 0))
                        group_occupied[group_key].add(best_slot.id)

                    improvements += 1
                    improved_this_round = True

            if not improved_this_round:
                break

        return improvements

    def _estimate_improvement(self, entry, new_slot):
        """Estimate the soft score improvement of moving an entry."""
        # Prefer morning slots (lower order)
        improvement = 0
        if new_slot.order < entry.time_slot.order:
            improvement += 2
        # Prefer less-used days (simplified heuristic)
        if new_slot.day_of_week != entry.time_slot.day_of_week:
            improvement += 1
        return improvement
