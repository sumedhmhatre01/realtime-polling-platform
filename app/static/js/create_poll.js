document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("poll-create-form");

  if (!form) {
    return;
  }

  const optionsContainer = document.getElementById("options-container");

  const addOptionButton = document.getElementById("add-option");

  const optionLimitMessage = document.getElementById("option-limit-message");

  const questionInput = document.getElementById("question");

  const questionCount = document.getElementById("question-count");

  const quizMode = document.getElementById("quiz-mode");

  const correctAnswerSection = document.getElementById(
    "correct-answer-section",
  );

  const correctAnswerOptions = document.getElementById(
    "correct-answer-options",
  );

  const multipleChoice = document.getElementById("multiple-choice");

  const MAX_OPTIONS = 10;

  // ==========================================================
  // Question character counter
  // ==========================================================

  function updateQuestionCount() {
    const length = questionInput.value.length;

    questionCount.textContent = `${length} / 500`;
  }

  questionInput.addEventListener("input", updateQuestionCount);

  updateQuestionCount();

  // ==========================================================
  // Option labels
  // ==========================================================

  function getOptionLabel(index) {
    return String.fromCharCode(65 + index);
  }

  function updateOptionRows() {
    const rows = optionsContainer.querySelectorAll(".option-row");

    rows.forEach((row, index) => {
      const label = row.querySelector(".option-index");

      if (label) {
        label.textContent = getOptionLabel(index);
      }

      const removeButton = row.querySelector(".remove-option");

      if (removeButton) {
        removeButton.disabled = rows.length <= 2;
      }
    });

    addOptionButton.disabled = rows.length >= MAX_OPTIONS;

    optionLimitMessage.hidden = rows.length < MAX_OPTIONS;

    updateCorrectAnswerOptions();
  }

  // ==========================================================
  // Add option
  // ==========================================================

  addOptionButton.addEventListener("click", () => {
    const rows = optionsContainer.querySelectorAll(".option-row");

    if (rows.length >= MAX_OPTIONS) {
      return;
    }

    const row = document.createElement("div");

    row.className = "option-row";

    row.innerHTML = `
                <span class="option-index">
                    ${getOptionLabel(rows.length)}
                </span>

                <input
                    type="text"
                    name="options"
                    maxlength="200"
                    placeholder="Option ${getOptionLabel(rows.length)}"
                    required
                >

                <button
                    type="button"
                    class="remove-option"
                    aria-label="Remove option"
                >
                    ×
                </button>
            `;

    optionsContainer.appendChild(row);

    updateOptionRows();
  });

  // ==========================================================
  // Remove option
  // ==========================================================

  optionsContainer.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-option");

    if (!button) {
      return;
    }

    const rows = optionsContainer.querySelectorAll(".option-row");

    if (rows.length <= 2) {
      return;
    }

    button.closest(".option-row").remove();

    updateOptionRows();
  });

  // ==========================================================
  // Quiz mode
  // ==========================================================

  function updateCorrectAnswerOptions() {
    correctAnswerOptions.innerHTML = "";

    const rows = optionsContainer.querySelectorAll(".option-row");

    const useMultipleAnswers = multipleChoice.checked;

    rows.forEach((row, index) => {
      const optionInput = row.querySelector('input[name="options"]');

      const wrapper = document.createElement("label");

      wrapper.className = "correct-answer-option";

      const inputType = useMultipleAnswers ? "checkbox" : "radio";

      wrapper.innerHTML = `
                <input
                    type="${inputType}"
                    name="correct_answer"
                    value="${index}"
                >

                <span>
                    ${getOptionLabel(index)}
                </span>

                <strong>
                    ${escapeHtml(optionInput.value)}
                </strong>
            `;

      correctAnswerOptions.appendChild(wrapper);
    });
  }

  function updateQuizVisibility() {
    correctAnswerSection.hidden = !quizMode.checked;

    if (quizMode.checked) {
      updateCorrectAnswerOptions();
    }
  }

  quizMode.addEventListener("change", updateQuizVisibility);

  multipleChoice.addEventListener("change", () => {
    if (quizMode.checked) {
      updateCorrectAnswerOptions();
    }
  });

  optionsContainer.addEventListener("input", (event) => {
    if (event.target.matches('input[name="options"]')) {
      updateCorrectAnswerOptions();
    }
  });

  // ==========================================================
  // Basic HTML escaping
  // ==========================================================

  function escapeHtml(value) {
    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
  }

  // ==========================================================
  // Form submission
  // ==========================================================

  form.addEventListener("submit", (event) => {
    const rows = optionsContainer.querySelectorAll(".option-row");

    if (rows.length < 2) {
      event.preventDefault();

      alert("Please provide at least two options.");

      return;
    }

    if (quizMode.checked) {
      const selectedAnswers = form.querySelectorAll(
        'input[name="correct_answer"]:checked',
      );

      if (selectedAnswers.length === 0) {
        event.preventDefault();

        alert("Please select at least one correct answer.");
      }
    }
  });

  // Initial state.
  updateOptionRows();
  updateQuizVisibility();
});
