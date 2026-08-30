import re

POLL_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6}$")


def validate_question(question: str, max_length: int = 500) -> str:
    """Validate and normalize a poll question."""

    if not isinstance(question, str):
        raise ValueError("Question must be text.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if len(question) > max_length:
        raise ValueError(f"Question cannot exceed {max_length} characters.")

    return question


def validate_options(
    options: list[str],
    max_options: int = 10,
    max_option_length: int = 200,
) -> list[str]:
    """Validate and normalize poll options."""

    if not isinstance(options, list):
        raise ValueError("Options must be provided as a list.")

    if len(options) < 2:
        raise ValueError("A poll must contain at least two options.")

    if len(options) > max_options:
        raise ValueError(f"A poll cannot contain more than {max_options} options.")

    cleaned_options = []

    for option in options:
        if not isinstance(option, str):
            raise ValueError("Each option must be text.")

        option = option.strip()

        if not option:
            raise ValueError("Poll options cannot be empty.")

        if len(option) > max_option_length:
            raise ValueError(
                f"Each option cannot exceed " f"{max_option_length} characters."
            )

        cleaned_options.append(option)

    normalized = [option.casefold() for option in cleaned_options]

    if len(normalized) != len(set(normalized)):
        raise ValueError("Poll options must be unique.")

    return cleaned_options


def validate_poll_code(poll_code: str) -> str:
    """Validate and normalize a poll code."""

    if not isinstance(poll_code, str):
        raise ValueError("Poll code must be text.")

    poll_code = poll_code.strip().upper()

    if not POLL_CODE_PATTERN.fullmatch(poll_code):
        raise ValueError("Invalid poll code.")

    return poll_code


def validate_time_limit(
    time_limit: int | None,
    max_duration: int = 3600,
) -> int | None:
    """Validate an optional poll time limit."""

    if time_limit is None:
        return None

    if isinstance(time_limit, bool):
        raise ValueError("Time limit must be a number.")

    if not isinstance(time_limit, int):
        raise ValueError("Time limit must be an integer.")

    if time_limit < 5:
        raise ValueError("Time limit must be at least 5 seconds.")

    if time_limit > max_duration:
        raise ValueError(f"Time limit cannot exceed " f"{max_duration} seconds.")

    return time_limit


def validate_boolean(
    value: bool,
    field_name: str,
) -> bool:
    """Validate a boolean configuration value."""

    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be true or false.")

    return value


def validate_correct_answers(
    correct_answer: list[int] | None,
    option_count: int,
    quiz_mode: bool,
    multiple_choice: bool,
) -> list[int] | None:
    """Validate quiz-mode correct answer indexes."""

    if not quiz_mode:
        if correct_answer is not None:
            raise ValueError("Correct answers are only allowed in quiz mode.")

        return None

    if not isinstance(correct_answer, list):
        raise ValueError("Quiz mode requires correct answers.")

    if not correct_answer:
        raise ValueError("At least one correct answer is required.")

    if not multiple_choice and len(correct_answer) != 1:
        raise ValueError("Single-choice quizzes can have only " "one correct answer.")

    if len(set(correct_answer)) != len(correct_answer):
        raise ValueError("Correct answers cannot contain duplicates.")

    for answer in correct_answer:
        if not isinstance(answer, int):
            raise ValueError("Correct answer indexes must be integers.")

        if answer < 0 or answer >= option_count:
            raise ValueError("Correct answer index is invalid.")

    return sorted(correct_answer)
