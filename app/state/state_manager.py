from app.state.participant_state import ParticipantState
from app.state.poll_state import PollState


class StateManager:
    """Coordinate all application in-memory state."""

    def __init__(self):
        self.polls = PollState()
        self.participants = ParticipantState()
