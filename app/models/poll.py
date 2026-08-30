from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Poll:
    """Represent a live poll and its configuration."""

    code: str
    question: str
    options: list[str]

    multiple_choice: bool = False
    anonymous_voting: bool = False
    allow_vote_changes: bool = False
    show_live_results: bool = True
    quiz_mode: bool = False

    correct_answer: Optional[list[int]] = None

    time_limit: Optional[int] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    started_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    status: str = "draft"

    votes: dict[str, list[int]] = field(default_factory=dict)

    vote_timestamps: list[datetime] = field(default_factory=list)

    participants: set[str] = field(default_factory=set)

    def is_active(self) -> bool:
        """Return True when the poll is active."""

        return self.status == "active"

    def is_paused(self) -> bool:
        """Return True when the poll is paused."""

        return self.status == "paused"

    def is_ended(self) -> bool:
        """Return True when the poll has ended."""

        return self.status in {
            "ended",
            "expired",
        }

    @property
    def participant_count(self) -> int:
        """Return the number of participants."""

        return len(self.participants)

    @property
    def vote_count(self) -> int:
        """Return the number of submitted votes."""

        return len(self.votes)
