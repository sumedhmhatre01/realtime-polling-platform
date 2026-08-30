from flask import request
from flask_socketio import emit

from app.sockets import socketio


def register_connection_events():
    """Register SocketIO connection lifecycle events."""

    @socketio.on("connect")
    def handle_connect():
        """Handle a new SocketIO connection."""

        emit(
            "connection_status",
            {
                "connected": True,
                "message": "Connected to live polling server.",
            },
        )

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle a SocketIO disconnection."""

        # We intentionally don't remove the participant here yet.
        #
        # A temporary network interruption should not immediately
        # destroy the participant's session.
        #
        # Participant lifecycle handling will be added after
        # poll-room membership is implemented.

        print(f"Socket disconnected: {request.sid}")
