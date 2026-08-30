import secrets
import string
from datetime import datetime, timedelta

from app.models.poll import Poll
from app.state.state_manager import StateManager
from app.utils.validators import (
    validate_boolean,
    validate_correct_answers,
    validate_options,
    validate_poll_code,
    validate_question,
    validate_time_limit,
)


class PollService:
    """Handle poll creation and lifecycle operations."""

    POLL_CODE_LENGTH = 6

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    def generate_poll_code(self) -> str:
        """Generate a unique six-character poll code."""

        characters = string.ascii_uppercase + string.digits

        for _ in range(100):
            code = "".join(
                secrets.choice(characters) for _ in range(self.POLL_CODE_LENGTH)
            )

            if not self.state.polls.exists(code):
                return code

        raise RuntimeError("Unable to generate a unique poll code.")

    def create_poll(
        self,
        question: str,
        options: list[str],
        multiple_choice: bool = False,
        anonymous_voting: bool = False,
        allow_vote_changes: bool = False,
        show_live_results: bool = True,
        quiz_mode: bool = False,
        correct_answer: list[int] | None = None,
        time_limit: int | None = None,
    ) -> Poll:
        """Validate, create, and store a new poll."""

        question = validate_question(question)

        options = validate_options(options)

        multiple_choice = validate_boolean(
            multiple_choice,
            "multiple_choice",
        )

        anonymous_voting = validate_boolean(
            anonymous_voting,
            "anonymous_voting",
        )

        allow_vote_changes = validate_boolean(
            allow_vote_changes,
            "allow_vote_changes",
        )

        show_live_results = validate_boolean(
            show_live_results,
            "show_live_results",
        )

        quiz_mode = validate_boolean(
            quiz_mode,
            "quiz_mode",
        )

        time_limit = validate_time_limit(time_limit)

        correct_answer = validate_correct_answers(
            correct_answer=correct_answer,
            option_count=len(options),
            quiz_mode=quiz_mode,
            multiple_choice=multiple_choice,
        )

        code = self.generate_poll_code()

        poll = Poll(
            code=code,
            question=question,
            options=options,
            multiple_choice=multiple_choice,
            anonymous_voting=anonymous_voting,
            allow_vote_changes=allow_vote_changes,
            show_live_results=show_live_results,
            quiz_mode=quiz_mode,
            correct_answer=correct_answer,
            time_limit=time_limit,
        )

        self.state.polls.add(poll)

        return poll

    def get_poll(
        self,
        poll_code: str,
    ) -> Poll | None:
        """Return a poll by its code."""

        poll_code = validate_poll_code(poll_code)

        return self.state.polls.get(poll_code)

    def start_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Start a draft poll."""

        poll = self._require_poll(poll_code)

        if poll.status != "draft":
            raise ValueError("Only draft polls can be started.")

        now = datetime.utcnow()

        poll.status = "active"
        poll.started_at = now

        if poll.time_limit:
            poll.ends_at = now + timedelta(seconds=poll.time_limit)

        return poll

    def pause_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Pause an active poll."""

        poll = self._require_poll(poll_code)

        if poll.status != "active":
            raise ValueError("Only active polls can be paused.")

        poll.status = "paused"
        poll.paused_at = datetime.utcnow()

        return poll

    def resume_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Resume a paused poll."""

        poll = self._require_poll(poll_code)

        if poll.status != "paused":
            raise ValueError("Only paused polls can be resumed.")

        now = datetime.utcnow()

        poll.status = "active"

        if poll.ends_at and poll.paused_at:
            paused_duration = now - poll.paused_at
            poll.ends_at += paused_duration

        poll.paused_at = None

        return poll

    def end_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """End a poll manually."""

        poll = self._require_poll(poll_code)

        if poll.status not in {"active", "paused"}:
            raise ValueError("Only active or paused polls can be ended.")

        poll.status = "ended"
        poll.ended_at = datetime.utcnow()

        return poll

    def expire_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Mark an active poll as expired."""

        poll = self._require_poll(poll_code)

        if poll.status != "active":
            return poll

        poll.status = "expired"
        poll.ended_at = datetime.utcnow()

        return poll

    def _require_poll(
        self,
        poll_code: str,
    ) -> Poll:
        """Return a poll or raise an error."""

        poll = self.get_poll(poll_code)

        if poll is None:
            raise ValueError("Poll not found.")

        return poll
