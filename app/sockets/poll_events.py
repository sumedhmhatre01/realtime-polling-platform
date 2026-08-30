from datetime import datetime

from flask import session
from flask_socketio import emit, join_room, leave_room

from app import state_manager
from app.services.analytics_service import AnalyticsService
from app.services.poll_service import PollService
from app.services.session_service import SessionService
from app.sockets import socketio

HOST_POLL_SESSION_KEY = "host_poll_code"


def _get_poll(poll_code):
    """Return a poll using a normalized poll code."""

    if not isinstance(poll_code, str):
        return None

    poll_code = poll_code.strip().upper()

    if not poll_code:
        return None

    return state_manager.polls.get(poll_code)


def _get_room(poll_code):
    """Return the SocketIO room name for a poll."""

    return f"poll:{poll_code.upper()}"


def _poll_state_payload(poll):
    """Build a safe poll-state payload for clients."""

    return {
        "poll_code": poll.code,
        "status": poll.status,
        "question": poll.question,
        "started_at": (poll.started_at.isoformat() if poll.started_at else None),
        "ends_at": (poll.ends_at.isoformat() if poll.ends_at else None),
        "paused_at": (poll.paused_at.isoformat() if poll.paused_at else None),
        "ended_at": (poll.ended_at.isoformat() if poll.ended_at else None),
    }


def _participant_count_payload(poll):
    """Build the participant count payload."""

    return {
        "poll_code": poll.code,
        "participant_count": poll.participant_count,
    }


def _results_payload(poll):
    """Build a fresh server-side analytics payload."""

    analytics_service = AnalyticsService(state_manager)

    analytics = analytics_service.get_poll_analytics(poll.code)

    return {
        "poll_code": poll.code,
        "analytics": analytics,
    }


def _get_current_participant():
    """Return the participant associated with the current session."""

    participant_id = session.get(SessionService.PARTICIPANT_SESSION_KEY)

    if not participant_id:
        return None

    return state_manager.participants.get(participant_id)


def _is_authorized_for_poll(poll):
    """
    Verify that the current SocketIO client belongs
    to the requested poll.

    A participant is authorized when their Flask session
    belongs to the poll.

    A host is authorized when their host session
    belongs to the poll.
    """

    participant = _get_current_participant()

    if participant is not None:
        return participant.poll_code == poll.code

    host_poll_code = session.get(HOST_POLL_SESSION_KEY)

    if host_poll_code:
        return str(host_poll_code).upper() == poll.code

    return False


def _broadcast_final_results(poll):
    """Broadcast the latest server-side analytics to the poll room."""

    room = _get_room(poll.code)

    socketio.emit(
        "results_updated",
        _results_payload(poll),
        to=room,
    )


def _expire_poll(poll_code):
    """
    Automatically expire a time-limited active poll.

    Return True when the poll was changed to expired.
    """

    poll = _get_poll(poll_code)

    if poll is None:
        return False

    if poll.status != "active":
        return False

    if poll.ends_at is None:
        return False

    if datetime.utcnow() < poll.ends_at:
        return False

    try:

        poll_service = PollService(state_manager)

        poll = poll_service.expire_poll(poll.code)

    except ValueError:
        return False

    room = _get_room(poll.code)

    payload = _poll_state_payload(poll)

    # ----------------------------------------------------------
    # Notify clients that the poll expired
    # ----------------------------------------------------------

    socketio.emit(
        "poll_expired",
        payload,
        to=room,
    )

    # ----------------------------------------------------------
    # Broadcast the final poll state
    # ----------------------------------------------------------

    socketio.emit(
        "poll_state",
        payload,
        to=room,
    )

    # ----------------------------------------------------------
    # Broadcast final analytics
    # ----------------------------------------------------------

    _broadcast_final_results(poll)

    return True


def _start_poll_expiration_watcher(poll):
    """
    Start a background watcher for a time-limited poll.

    The watcher periodically checks the server-side poll state
    and expires the poll when ends_at is reached.
    """

    if poll.time_limit is None:
        return

    poll_code = poll.code

    def expiration_watcher():

        while True:

            current_poll = _get_poll(poll_code)

            if current_poll is None:
                return

            if current_poll.status != "active":
                return

            if current_poll.ends_at is None:
                return

            remaining_seconds = (
                current_poll.ends_at - datetime.utcnow()
            ).total_seconds()

            if remaining_seconds <= 0:

                _expire_poll(poll_code)

                return

            sleep_seconds = min(
                max(
                    remaining_seconds,
                    0.25,
                ),
                0.5,
            )

            socketio.sleep(sleep_seconds)

    socketio.start_background_task(expiration_watcher)


def register_poll_events():
    """Register poll-related SocketIO events."""

    @socketio.on("join_poll")
    def handle_join_poll(data):
        """Join an authorized client to a poll room."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        poll = _get_poll(poll_code)

        if poll is None:
            emit(
                "socket_error",
                {"message": "Poll not found."},
            )
            return

        if not _is_authorized_for_poll(poll):
            emit(
                "socket_error",
                {"message": ("You are not authorized " "to join this poll.")},
            )
            return

        room = _get_room(poll_code)

        join_room(room)

        emit(
            "poll_room_joined",
            {
                "poll_code": poll.code,
                "status": poll.status,
                "message": "Joined poll room.",
            },
        )

        emit(
            "poll_state",
            _poll_state_payload(poll),
        )

        emit(
            "participant_count_updated",
            _participant_count_payload(poll),
        )

        socketio.emit(
            "participant_count_updated",
            _participant_count_payload(poll),
            to=room,
        )

        socketio.emit(
            "results_updated",
            _results_payload(poll),
            to=room,
        )

    @socketio.on("leave_poll")
    def handle_leave_poll(data):
        """Leave a poll SocketIO room."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        if not poll_code:
            return

        poll = _get_poll(poll_code)

        if poll is None:
            return

        if not _is_authorized_for_poll(poll):
            emit(
                "socket_error",
                {"message": ("You are not authorized " "for this poll.")},
            )
            return

        room = _get_room(poll_code)

        leave_room(room)

        emit(
            "poll_room_left",
            {
                "poll_code": poll.code,
            },
        )

    @socketio.on("start_poll")
    def handle_start_poll(data):
        """Start a poll and broadcast the new state."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        poll = _get_poll(poll_code)

        if poll is None:
            emit(
                "socket_error",
                {"message": "Poll not found."},
            )
            return

        host_poll_code = session.get(HOST_POLL_SESSION_KEY)

        if not host_poll_code or str(host_poll_code).upper() != poll.code:
            emit(
                "socket_error",
                {"message": ("Only the poll host can " "start this poll.")},
            )
            return

        try:

            poll_service = PollService(state_manager)

            poll = poll_service.start_poll(poll.code)

        except ValueError as exc:

            emit(
                "socket_error",
                {"message": str(exc)},
            )
            return

        except Exception:

            emit(
                "socket_error",
                {"message": ("Unable to start the poll.")},
            )
            return

        room = _get_room(poll.code)

        payload = _poll_state_payload(poll)

        socketio.emit(
            "poll_started",
            payload,
            to=room,
        )

        socketio.emit(
            "poll_state",
            payload,
            to=room,
        )

        _start_poll_expiration_watcher(poll)

    @socketio.on("pause_poll")
    def handle_pause_poll(data):
        """Pause an active poll."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        poll = _get_poll(poll_code)

        if poll is None:
            emit(
                "socket_error",
                {"message": "Poll not found."},
            )
            return

        host_poll_code = session.get(HOST_POLL_SESSION_KEY)

        if not host_poll_code or str(host_poll_code).upper() != poll.code:
            emit(
                "socket_error",
                {"message": ("Only the poll host can " "pause this poll.")},
            )
            return

        try:

            poll_service = PollService(state_manager)

            poll = poll_service.pause_poll(poll.code)

        except ValueError as exc:

            emit(
                "socket_error",
                {"message": str(exc)},
            )
            return

        except Exception:

            emit(
                "socket_error",
                {"message": ("Unable to pause the poll.")},
            )
            return

        room = _get_room(poll.code)

        payload = _poll_state_payload(poll)

        socketio.emit(
            "poll_paused",
            payload,
            to=room,
        )

        socketio.emit(
            "poll_state",
            payload,
            to=room,
        )

    @socketio.on("resume_poll")
    def handle_resume_poll(data):
        """Resume a paused poll."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        poll = _get_poll(poll_code)

        if poll is None:
            emit(
                "socket_error",
                {"message": "Poll not found."},
            )
            return

        host_poll_code = session.get(HOST_POLL_SESSION_KEY)

        if not host_poll_code or str(host_poll_code).upper() != poll.code:
            emit(
                "socket_error",
                {"message": ("Only the poll host can " "resume this poll.")},
            )
            return

        try:

            poll_service = PollService(state_manager)

            poll = poll_service.resume_poll(poll.code)

        except ValueError as exc:

            emit(
                "socket_error",
                {"message": str(exc)},
            )
            return

        except Exception:

            emit(
                "socket_error",
                {"message": ("Unable to resume the poll.")},
            )
            return

        room = _get_room(poll.code)

        payload = _poll_state_payload(poll)

        socketio.emit(
            "poll_resumed",
            payload,
            to=room,
        )

        socketio.emit(
            "poll_state",
            payload,
            to=room,
        )

        _start_poll_expiration_watcher(poll)

    @socketio.on("end_poll")
    def handle_end_poll(data):
        """End a poll and broadcast the final state and results."""

        if not isinstance(data, dict):
            emit(
                "socket_error",
                {"message": "Invalid request."},
            )
            return

        poll_code = (
            str(
                data.get(
                    "poll_code",
                    "",
                )
            )
            .strip()
            .upper()
        )

        poll = _get_poll(poll_code)

        if poll is None:
            emit(
                "socket_error",
                {"message": "Poll not found."},
            )
            return

        host_poll_code = session.get(HOST_POLL_SESSION_KEY)

        if not host_poll_code or str(host_poll_code).upper() != poll.code:
            emit(
                "socket_error",
                {"message": ("Only the poll host can " "end this poll.")},
            )
            return

        try:

            poll_service = PollService(state_manager)

            poll = poll_service.end_poll(poll.code)

        except ValueError as exc:

            emit(
                "socket_error",
                {"message": str(exc)},
            )
            return

        except Exception:

            emit(
                "socket_error",
                {"message": ("Unable to end the poll.")},
            )
            return

        room = _get_room(poll.code)

        payload = _poll_state_payload(poll)

        socketio.emit(
            "poll_ended",
            payload,
            to=room,
        )

        socketio.emit(
            "poll_state",
            payload,
            to=room,
        )

        # ------------------------------------------------------
        # Broadcast final analytics
        # ------------------------------------------------------

        _broadcast_final_results(poll)
