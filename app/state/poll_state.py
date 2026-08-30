from threading import RLock
from typing import Optional

from app.models.poll import Poll


class PollState:
    """Thread-safe in-memory storage for active polls."""

    def __init__(self):
        self._polls: dict[str, Poll] = {}
        self._lock = RLock()

    def add(self, poll: Poll) -> None:
        """Add a poll to the state."""

        with self._lock:
            self._polls[poll.code] = poll

    def get(self, poll_code: str) -> Optional[Poll]:
        """Return a poll by its code."""

        with self._lock:
            return self._polls.get(poll_code)

    def remove(self, poll_code: str) -> Optional[Poll]:
        """Remove and return a poll."""

        with self._lock:
            return self._polls.pop(poll_code, None)

    def exists(self, poll_code: str) -> bool:
        """Return whether a poll exists."""

        with self._lock:
            return poll_code in self._polls

    def all(self) -> list[Poll]:
        """Return all currently stored polls."""

        with self._lock:
            return list(self._polls.values())

    def count(self) -> int:
        """Return the number of stored polls."""

        with self._lock:
            return len(self._polls)
