from collections import Counter
from datetime import datetime

from app.state.state_manager import StateManager


class AnalyticsService:
    """Calculate server-side analytics for a poll."""

    def __init__(
        self,
        state_manager: StateManager,
    ):
        self.state = state_manager

    def get_poll_analytics(
        self,
        poll_code: str,
    ) -> dict:
        """
        Return calculated analytics for a poll.

        All calculations are performed from server-side
        poll state. Client-supplied analytics are never trusted.
        """

        poll = self._get_poll(poll_code)

        total_participants = len(poll.participants)

        total_votes = len(poll.votes)

        response_rate = self._calculate_response_rate(
            total_votes,
            total_participants,
        )

        option_votes = self._calculate_option_votes(poll)

        option_percentages = self._calculate_option_percentages(
            option_votes,
            total_votes,
        )

        leading_option = self._calculate_leading_option(
            poll,
            option_votes,
        )

        voting_rate = self._calculate_voting_rate(poll)

        votes_over_time = self._calculate_votes_over_time(poll)

        return {
            "poll_code": poll.code,
            "total_participants": (total_participants),
            "total_votes": total_votes,
            "response_rate": response_rate,
            "option_votes": option_votes,
            "option_percentages": (option_percentages),
            "leading_option": (leading_option),
            "voting_rate": voting_rate,
            "votes_over_time": (votes_over_time),
        }

    def _get_poll(self, poll_code):
        """Return a poll or raise an error."""

        if not isinstance(
            poll_code,
            str,
        ):
            raise ValueError("Invalid poll code.")

        normalized_code = poll_code.strip().upper()

        if not normalized_code:
            raise ValueError("Poll code is required.")

        poll = self.state.polls.get(normalized_code)

        if poll is None:
            raise ValueError("Poll not found.")

        return poll

    @staticmethod
    def _calculate_response_rate(
        total_votes: int,
        total_participants: int,
    ) -> float:
        """Calculate the participant response rate."""

        if total_participants <= 0:
            return 0.0

        return round(
            (total_votes / total_participants) * 100,
            2,
        )

    @staticmethod
    def _calculate_option_votes(
        poll,
    ) -> list[int]:
        """
        Count how many votes each option received.

        For multiple-choice polls, one participant can
        contribute to more than one option.
        """

        counts = [0 for _ in poll.options]

        for selected_options in poll.votes.values():

            if not isinstance(
                selected_options,
                list,
            ):
                continue

            for option_index in selected_options:

                if isinstance(
                    option_index,
                    int,
                ) and 0 <= option_index < len(counts):
                    counts[option_index] += 1

        return counts

    @staticmethod
    def _calculate_option_percentages(
        option_votes: list[int],
        total_votes: int,
    ) -> list[float]:
        """Calculate percentage for each option."""

        if total_votes <= 0:
            return [0.0 for _ in option_votes]

        return [
            round(
                (vote_count / total_votes) * 100,
                2,
            )
            for vote_count in option_votes
        ]

    @staticmethod
    def _calculate_leading_option(
        poll,
        option_votes: list[int],
    ) -> dict | None:
        """Return the current leading option."""

        if not option_votes:
            return None

        highest_votes = max(option_votes)

        if highest_votes <= 0:
            return None

        leading_indexes = [
            index
            for index, vote_count in enumerate(option_votes)
            if vote_count == highest_votes
        ]

        return {
            "indexes": leading_indexes,
            "options": [poll.options[index] for index in leading_indexes],
            "votes": highest_votes,
        }

    @staticmethod
    def _calculate_voting_rate(
        poll,
    ) -> float:
        """
        Calculate average votes per second.

        The calculation uses the time between the first
        and latest recorded vote.
        """

        timestamps = poll.vote_timestamps

        if len(timestamps) < 2:
            return float(len(timestamps)) if timestamps else 0.0

        first_vote = min(timestamps)

        latest_vote = max(timestamps)

        elapsed_seconds = (latest_vote - first_vote).total_seconds()

        if elapsed_seconds <= 0:
            return float(len(timestamps))

        return round(
            len(timestamps) / elapsed_seconds,
            2,
        )

    @staticmethod
    def _calculate_votes_over_time(
        poll,
    ) -> list[dict]:
        """
        Return vote timestamps in a frontend-friendly format.
        """

        timestamps = poll.vote_timestamps

        return [
            {
                "timestamp": timestamp.isoformat(),
                "count": index + 1,
            }
            for index, timestamp in enumerate(timestamps)
        ]
