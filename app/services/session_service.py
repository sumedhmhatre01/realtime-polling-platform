from flask import session

from app.models.participant import Participant
from app.services.security_service import SecurityService
from app.state.state_manager import StateManager
from app.utils.validators import validate_poll_code


class SessionService:
    """Manage participant identities and sessions."""

    PARTICIPANT_SESSION_KEY = "participant_id"

    def __init__(
        self,
        state_manager: StateManager,
    ):
        self.state = state_manager

    def get_participant_id(self) -> str | None:
        """Return the current participant session ID."""

        return session.get(self.PARTICIPANT_SESSION_KEY)

    def create_participant(
        self,
        poll_code: str,
    ) -> Participant:
        """Create a participant for a poll."""

        poll_code = validate_poll_code(poll_code)

        poll = self.state.polls.get(poll_code)

        if poll is None:
            raise ValueError("Poll not found.")

        participant_id = SecurityService.generate_participant_id()

        participant = Participant(
            participant_id=participant_id,
            poll_code=poll_code,
        )

        self.state.participants.add(participant)

        poll.participants.add(participant_id)

        session[self.PARTICIPANT_SESSION_KEY] = participant_id

        return participant

    def get_current_participant(
        self,
    ) -> Participant | None:
        """Return the current participant."""

        participant_id = self.get_participant_id()

        if not participant_id:
            return None

        return self.state.participants.get(participant_id)

    def get_current_poll(
        self,
    ):
        """Return the poll for the current participant."""

        participant = self.get_current_participant()

        if participant is None:
            return None

        return self.state.polls.get(participant.poll_code)

    def leave_participant(self) -> None:
        """Remove the current participant."""

        participant_id = self.get_participant_id()

        if not participant_id:
            return

        participant = self.state.participants.get(participant_id)

        if participant:
            poll = self.state.polls.get(participant.poll_code)

            if poll:
                poll.participants.discard(participant_id)

        self.state.participants.remove(participant_id)

        session.pop(
            self.PARTICIPANT_SESSION_KEY,
            None,
        )
