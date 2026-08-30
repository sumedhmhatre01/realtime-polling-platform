from dataclasses import dataclass
from datetime import datetime


@dataclass
class Participant:
    """Represent a participant in a polling session."""

    participant_id: str
    poll_code: str
    has_voted: bool = False
    joined_at: datetime | None = None
    last_vote_at: datetime | None = None
