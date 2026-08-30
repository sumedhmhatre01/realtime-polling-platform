from datetime import datetime

from flask import Flask

from app.config import Config
from app.state.state_manager import StateManager
from app.sockets import socketio

state_manager = StateManager()


def _get_poll_room(poll_code: str) -> str:
    """Return the SocketIO room name for a poll."""

    return f"poll:{poll_code.upper()}"


def _poll_state_payload(poll):
    """Build a safe poll-state payload for SocketIO clients."""

    return {
        "poll_code": poll.code,
        "status": poll.status,
        "question": poll.question,
        "started_at": (poll.started_at.isoformat() if poll.started_at else None),
        "ends_at": (poll.ends_at.isoformat() if poll.ends_at else None),
        "paused_at": (poll.paused_at.isoformat() if poll.paused_at else None),
        "ended_at": (poll.ended_at.isoformat() if poll.ended_at else None),
    }


def _start_poll_expiration_worker():
    """Start the background worker that expires time-limited polls."""

    def expiration_worker():
        from app.services.poll_service import PollService

        poll_service = PollService(state_manager)

        while True:
            socketio.sleep(1)

            now = datetime.utcnow()

            for poll in state_manager.polls.all():
                if poll.status != "active":
                    continue

                if poll.ends_at is None:
                    continue

                if now < poll.ends_at:
                    continue

                try:
                    poll = poll_service.expire_poll(poll.code)

                except ValueError:
                    continue

                room = _get_poll_room(poll.code)

                payload = _poll_state_payload(poll)

                socketio.emit(
                    "poll_expired",
                    payload,
                    to=room,
                )

                socketio.emit(
                    "poll_state",
                    payload,
                    to=room,
                )

    socketio.start_background_task(expiration_worker)


def create_app(config_class=Config):
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config.from_object(config_class)

    # ----------------------------------------------------------
    # Initialize SocketIO with Flask
    # ----------------------------------------------------------

    socketio.init_app(
        app,
        cors_allowed_origins=[],
    )

    # ----------------------------------------------------------
    # Register routes
    # ----------------------------------------------------------

    from app.routes.main import main_bp
    from app.routes.host import host_bp
    from app.routes.participant import participant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(host_bp)
    app.register_blueprint(participant_bp)

    # ----------------------------------------------------------
    # Register SocketIO events
    # ----------------------------------------------------------

    from app.sockets.connection_events import (
        register_connection_events,
    )

    from app.sockets.poll_events import (
        register_poll_events,
    )

    register_connection_events()
    register_poll_events()

    # ----------------------------------------------------------
    # Start poll expiration worker
    # ----------------------------------------------------------

    _start_poll_expiration_worker()

    return app
