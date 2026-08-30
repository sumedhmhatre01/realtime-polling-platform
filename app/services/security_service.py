import secrets

from app.utils.validators import validate_poll_code


class SecurityService:
    """Handle security-sensitive identity and validation operations."""

    PARTICIPANT_ID_BYTES = 16

    @staticmethod
    def generate_participant_id() -> str:
        """Generate a cryptographically secure participant ID."""

        return secrets.token_urlsafe(SecurityService.PARTICIPANT_ID_BYTES)

    @staticmethod
    def validate_poll_access_code(
        poll_code: str,
    ) -> str:
        """Validate a participant-supplied poll code."""

        return validate_poll_code(poll_code)

    @staticmethod
    def validate_option_indexes(
        selected_options: list[int],
        option_count: int,
        multiple_choice: bool,
    ) -> list[int]:
        """Validate submitted answer indexes."""

        if not isinstance(selected_options, list):
            raise ValueError("Selected options must be a list.")

        if not selected_options:
            raise ValueError("At least one option must be selected.")

        if not multiple_choice and len(selected_options) != 1:
            raise ValueError("Only one option can be selected.")

        if len(set(selected_options)) != len(selected_options):
            raise ValueError("Duplicate options are not allowed.")

        for option_index in selected_options:
            if not isinstance(option_index, int):
                raise ValueError("Option indexes must be integers.")

            if option_index < 0 or option_index >= option_count:
                raise ValueError("Invalid option selected.")

        return sorted(selected_options)
