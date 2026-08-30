from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import state_manager
from app.services.analytics_service import AnalyticsService
from app.services.poll_service import PollService

host_bp = Blueprint(
    "host",
    __name__,
    url_prefix="/host",
)


HOST_POLL_SESSION_KEY = "host_poll_code"


@host_bp.route(
    "/create",
    methods=["GET", "POST"],
)
def create_poll():
    """Render and process the poll creation form."""

    error = None

    if request.method == "POST":
        try:
            question = request.form.get(
                "question",
                "",
            )

            options = request.form.getlist("options")

            multiple_choice = request.form.get("multiple_choice") == "on"

            anonymous_voting = request.form.get("anonymous_voting") == "on"

            allow_vote_changes = request.form.get("allow_vote_changes") == "on"

            show_live_results = request.form.get("show_live_results") == "on"

            quiz_mode = request.form.get("quiz_mode") == "on"

            time_limit_raw = request.form.get(
                "time_limit",
                "",
            ).strip()

            time_limit = int(time_limit_raw) if time_limit_raw else None

            correct_answer_raw = request.form.getlist("correct_answer")

            correct_answer = [int(index) for index in correct_answer_raw]

            if not quiz_mode:
                correct_answer = None

            service = PollService(state_manager)

            poll = service.create_poll(
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

            # --------------------------------------------------
            # Associate the current browser session with the poll
            # --------------------------------------------------

            session[HOST_POLL_SESSION_KEY] = poll.code

            return redirect(
                url_for(
                    "host.dashboard",
                    poll_code=poll.code,
                )
            )

        except (ValueError, TypeError) as exc:
            error = str(exc)

        except Exception:
            current_app.logger.exception("Unexpected error during poll creation.")

            error = "Something went wrong while creating " "the poll. Please try again."

    return render_template(
        "create_poll.html",
        error=error,
    )


@host_bp.route("/dashboard")
def dashboard_without_poll():
    """Show the dashboard entry page."""

    host_poll_code = session.get(HOST_POLL_SESSION_KEY)

    if host_poll_code:
        return redirect(
            url_for(
                "host.dashboard",
                poll_code=host_poll_code,
            )
        )

    return redirect(url_for("host.create_poll"))


@host_bp.route("/dashboard/<poll_code>")
def dashboard(poll_code):
    """Render the dashboard for a specific poll."""

    poll_code = poll_code.strip().upper()

    # ----------------------------------------------------------
    # Host session protection
    # ----------------------------------------------------------

    host_poll_code = session.get(HOST_POLL_SESSION_KEY)

    if host_poll_code != poll_code:
        return (
            render_template(
                "host_dashboard.html",
                poll=None,
                error=("You do not have access to " "this host dashboard."),
            ),
            403,
        )

    service = PollService(state_manager)

    poll = service.get_poll(poll_code)

    if poll is None:
        session.pop(
            HOST_POLL_SESSION_KEY,
            None,
        )

        return (
            render_template(
                "host_dashboard.html",
                poll=None,
                error="Poll not found.",
            ),
            404,
        )

    # ----------------------------------------------------------
    # Calculate current analytics
    # ----------------------------------------------------------

    analytics_service = AnalyticsService(state_manager)

    analytics = analytics_service.get_poll_analytics(
        poll.code,
    )

    return render_template(
        "host_dashboard.html",
        poll=poll,
        analytics=analytics,
    )
