from datetime import datetime

from app.models.participant import Participant
from app.models.poll import Poll
from app.services.security_service import SecurityService
from app.state.state_manager import StateManager


class VoteService:
    """Handle server-side vote validation and submission."""

    def __init__(
        self,
        state_manager: StateManager,
    ):
        self.state = state_manager

    def submit_vote(
        self,
        poll_code: str,
        participant_id: str,
        selected_options: list[int],
    ) -> Poll:
        """
        Validate and submit a participant vote.

        The server is authoritative for every voting rule.
        """

        poll = self._get_poll(poll_code)

        participant = self._get_participant(participant_id)

        self._validate_participant_poll(
            participant,
            poll,
        )

        self._validate_poll_status(poll)

        selected_options = SecurityService.validate_option_indexes(
            selected_options=selected_options,
            option_count=len(poll.options),
            multiple_choice=poll.multiple_choice,
        )

        self._validate_existing_vote(
            poll,
            participant,
        )

        now = datetime.utcnow()

        poll.votes[participant.participant_id] = selected_options

        poll.vote_timestamps.append(now)

        participant.has_voted = True
        participant.last_vote_at = now

        return poll

    def change_vote(
        self,
        poll_code: str,
        participant_id: str,
        selected_options: list[int],
    ) -> Poll:
        """Change an existing participant vote."""

        poll = self._get_poll(poll_code)

        participant = self._get_participant(participant_id)

        self._validate_participant_poll(
            participant,
            poll,
        )

        self._validate_poll_status(poll)

        if not poll.allow_vote_changes:
            raise ValueError("Vote changes are not allowed for this poll.")

        if not participant.has_voted:
            raise ValueError("A vote has not been submitted yet.")

        selected_options = SecurityService.validate_option_indexes(
            selected_options=selected_options,
            option_count=len(poll.options),
            multiple_choice=poll.multiple_choice,
        )

        now = datetime.utcnow()

        poll.votes[participant.participant_id] = selected_options

        participant.last_vote_at = now

        return poll

    def has_voted(
        self,
        poll_code: str,
        participant_id: str,
    ) -> bool:
        """Return whether a participant has voted."""

        poll = self._get_poll(poll_code)

        return participant_id in poll.votes

    def get_vote(
        self,
        poll_code: str,
        participant_id: str,
    ) -> list[int] | None:
        """Return a participant's selected options."""

        poll = self._get_poll(poll_code)

        return poll.votes.get(participant_id)

    def get_vote_count(
        self,
        poll_code: str,
    ) -> int:
        """Return the total number of submitted votes."""

        poll = self._get_poll(poll_code)

        return len(poll.votes)

    def _get_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Return a poll or raise an error."""

        poll = self.state.polls.get(poll_code.upper())

        if poll is None:
            raise ValueError("Poll not found.")

        return poll

    def _get_participant(
        self,
        participant_id: str,
    ) -> Participant:
        """Return a participant or raise an error."""

        participant = self.state.participants.get(participant_id)

        if participant is None:
            raise ValueError("Participant session not found.")

        return participant

    @staticmethod
    def _validate_participant_poll(
        participant: Participant,
        poll: Poll,
    ) -> None:
        """Ensure the participant belongs to this poll."""

        if participant.poll_code != poll.code:
            raise ValueError("Participant does not belong to this poll.")

    @staticmethod
    def _validate_poll_status(
        poll: Poll,
    ) -> None:
        """Ensure the poll accepts votes."""

        if poll.status != "active":

            if poll.status == "paused":
                raise ValueError("Voting is temporarily paused.")

            if poll.status == "ended":
                raise ValueError("This poll has ended.")

            if poll.status == "expired":
                raise ValueError("This poll has expired.")

            raise ValueError("This poll is not accepting votes.")

        if poll.ends_at is not None and datetime.utcnow() >= poll.ends_at:
            poll.status = "expired"
            poll.ended_at = datetime.utcnow()

            raise ValueError("This poll has expired.")

    @staticmethod
    def _validate_existing_vote(
        poll: Poll,
        participant: Participant,
    ) -> None:
        """Prevent duplicate votes."""

        if participant.participant_id in poll.votes:

            if poll.allow_vote_changes:
                raise ValueError("A vote already exists. " "Use vote change instead.")

            raise ValueError("You have already voted.")
