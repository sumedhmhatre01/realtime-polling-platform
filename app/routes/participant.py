from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)

from app import state_manager
from app.services.analytics_service import AnalyticsService
from app.services.session_service import SessionService
from app.services.vote_service import VoteService
from app.sockets import socketio

participant_bp = Blueprint(
    "participant",
    __name__,
    url_prefix="/participant",
)


def _get_poll_room(poll_code: str) -> str:
    """Return the SocketIO room name for a poll."""

    return f"poll:{poll_code.upper()}"


def _build_results_payload(poll):
    """Build a safe server-side analytics payload."""

    analytics_service = AnalyticsService(state_manager)

    analytics = analytics_service.get_poll_analytics(poll.code)

    return {
        "poll_code": poll.code,
        "analytics": analytics,
    }


@participant_bp.route(
    "/join",
    methods=["GET", "POST"],
)
def join_poll():
    """Allow a participant to join a poll."""

    error = None

    if request.method == "POST":

        poll_code = request.form.get(
            "poll_code",
            "",
        ).strip()

        try:

            session_service = SessionService(state_manager)

            participant = session_service.create_participant(poll_code)

            return redirect(
                url_for(
                    "participant.participant_poll",
                    poll_code=participant.poll_code,
                )
            )

        except ValueError as exc:

            error = str(exc)

        except Exception:

            error = "Unable to join the poll. " "Please try again."

    return render_template(
        "join_poll.html",
        error=error,
    )


@participant_bp.route(
    "/poll/<poll_code>",
    methods=["GET"],
)
def participant_poll(poll_code):
    """Render the participant poll page."""

    session_service = SessionService(state_manager)

    participant = session_service.get_current_participant()

    if participant is None:

        return redirect(url_for("participant.join_poll"))

    poll_code = poll_code.strip().upper()

    if participant.poll_code != poll_code:

        return redirect(url_for("participant.join_poll"))

    poll = state_manager.polls.get(poll_code)

    if poll is None:

        return (
            render_template(
                "participant_poll.html",
                poll=None,
                participant=None,
                current_vote=None,
                analytics=None,
                error="Poll not found.",
            ),
            404,
        )

    vote_service = VoteService(state_manager)

    current_vote = vote_service.get_vote(
        poll_code=poll.code,
        participant_id=participant.participant_id,
    )

    analytics_service = AnalyticsService(state_manager)

    analytics = analytics_service.get_poll_analytics(poll.code)

    return render_template(
        "participant_poll.html",
        poll=poll,
        participant=participant,
        current_vote=current_vote,
        analytics=analytics,
        error=None,
    )


@participant_bp.route(
    "/poll/<poll_code>/vote",
    methods=["POST"],
)
def submit_vote(poll_code):
    """Submit or change a participant vote."""

    session_service = SessionService(state_manager)

    participant = session_service.get_current_participant()

    if participant is None:

        return redirect(url_for("participant.join_poll"))

    poll_code = poll_code.strip().upper()

    if participant.poll_code != poll_code:

        return redirect(url_for("participant.join_poll"))

    selected_options_raw = request.form.getlist("selected_options")

    try:

        selected_options = [int(option) for option in selected_options_raw]

        vote_service = VoteService(state_manager)

        was_already_voted = participant.has_voted

        # ====================================================
        # Submit or change vote
        # ====================================================

        if was_already_voted:

            poll = vote_service.change_vote(
                poll_code=poll_code,
                participant_id=participant.participant_id,
                selected_options=selected_options,
            )

        else:

            poll = vote_service.submit_vote(
                poll_code=poll_code,
                participant_id=participant.participant_id,
                selected_options=selected_options,
            )

        # ====================================================
        # Calculate fresh analytics
        # ====================================================

        results_payload = _build_results_payload(poll)

        room = _get_poll_room(poll.code)

        # ====================================================
        # Notify clients
        # ====================================================

        if was_already_voted:

            socketio.emit(
                "vote_updated",
                {
                    "poll_code": poll.code,
                    "participant_id": (participant.participant_id),
                },
                to=room,
            )

        else:

            socketio.emit(
                "vote_submitted",
                {
                    "poll_code": poll.code,
                    "participant_id": (participant.participant_id),
                },
                to=room,
            )

        # ====================================================
        # Broadcast fresh results
        # ====================================================

        socketio.emit(
            "results_updated",
            results_payload,
            to=room,
        )

        return redirect(
            url_for(
                "participant.participant_poll",
                poll_code=poll.code,
            )
        )

    except (ValueError, TypeError) as exc:

        poll = state_manager.polls.get(poll_code)

        analytics = None

        if poll is not None:

            analytics_service = AnalyticsService(state_manager)

            analytics = analytics_service.get_poll_analytics(poll.code)

        return (
            render_template(
                "participant_poll.html",
                poll=poll,
                participant=participant,
                current_vote=selected_options_raw,
                analytics=analytics,
                error=str(exc),
            ),
            400,
        )

    except Exception:

        poll = state_manager.polls.get(poll_code)

        analytics = None

        if poll is not None:

            analytics_service = AnalyticsService(state_manager)

            analytics = analytics_service.get_poll_analytics(poll.code)

        return (
            render_template(
                "participant_poll.html",
                poll=poll,
                participant=participant,
                current_vote=None,
                analytics=analytics,
                error=("Unable to submit your vote. " "Please try again."),
            ),
            500,
        )
