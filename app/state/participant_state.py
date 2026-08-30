from threading import RLock
from typing import Optional

from app.models.participant import Participant


class ParticipantState:
    """Thread-safe in-memory participant storage."""

    def __init__(self):
        self._participants: dict[str, Participant] = {}
        self._lock = RLock()

    def add(self, participant: Participant) -> None:
        """Add a participant."""

        with self._lock:
            self._participants[participant.participant_id] = participant

    def get(
        self,
        participant_id: str,
    ) -> Optional[Participant]:
        """Return a participant by ID."""

        with self._lock:
            return self._participants.get(participant_id)

    def remove(
        self,
        participant_id: str,
    ) -> Optional[Participant]:
        """Remove and return a participant."""

        with self._lock:
            return self._participants.pop(participant_id, None)

    def all_for_poll(
        self,
        poll_code: str,
    ) -> list[Participant]:
        """Return all participants belonging to a poll."""

        with self._lock:
            return [
                participant
                for participant in self._participants.values()
                if participant.poll_code == poll_code
            ]

    def count_for_poll(self, poll_code: str) -> int:
        """Return participant count for a poll."""

        return len(self.all_for_poll(poll_code))
