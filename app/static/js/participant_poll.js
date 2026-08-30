/* ============================================================
   PARTICIPANT POLL
   Real-Time Polling and Analytics System
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  const pollCodeElement = document.getElementById("poll-code");

  if (!pollCodeElement) {
    return;
  }

  const pollCode =
    pollCodeElement.dataset.pollCode ||
    pollCodeElement.textContent.trim().toUpperCase();

  const statusText = document.getElementById("poll-status-text");

  const statusDot = document.getElementById("poll-status-dot");

  const votingContainer = document.getElementById("voting-container");

  const stateMessage = document.getElementById("poll-state-message");

  const liveResults = document.getElementById("participant-live-results");

  const liveMessage = document.getElementById("participant-live-message");

  /* ==========================================================
     Status
     ========================================================== */

  function updateStatus(status) {
    if (!status) {
      return;
    }

    if (statusText) {
      statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }

    if (statusDot) {
      statusDot.classList.remove("active", "paused", "ended", "expired");

      if (
        status === "active" ||
        status === "paused" ||
        status === "ended" ||
        status === "expired"
      ) {
        statusDot.classList.add(status);
      }
    }
  }

  /* ==========================================================
     Show Voting Interface
     ========================================================== */

  function showVotingInterface() {
    if (votingContainer) {
      votingContainer.hidden = false;
      votingContainer.style.display = "";
    }

    if (stateMessage) {
      stateMessage.hidden = true;
      stateMessage.style.display = "none";
    }
  }

  /* ==========================================================
     Hide Voting Interface
     ========================================================== */

  function hideVotingInterface() {
    if (votingContainer) {
      votingContainer.hidden = true;
      votingContainer.style.display = "none";
    }
  }

  /* ==========================================================
     Show State Message
     ========================================================== */

  function showStateMessage(title, message) {
    hideVotingInterface();

    if (!stateMessage) {
      return;
    }

    stateMessage.hidden = false;
    stateMessage.style.display = "";

    const titleElement = stateMessage.querySelector("h2");

    const messageElement = stateMessage.querySelector("p");

    if (titleElement) {
      titleElement.textContent = title;
    }

    if (messageElement) {
      messageElement.textContent = message;
    }
  }

  /* ==========================================================
     Handle Poll State
     ========================================================== */

  function handlePollState(status) {
    updateStatus(status);

    switch (status) {
      case "active":
        showVotingInterface();
        break;

      case "paused":
        showStateMessage(
          "Voting is paused",
          "The host has temporarily paused this poll. You can continue when voting resumes.",
        );
        break;

      case "ended":
        showStateMessage(
          "Poll ended",
          "This poll is no longer accepting votes.",
        );
        break;

      case "expired":
        showStateMessage(
          "Poll expired",
          "The time limit for this poll has expired.",
        );
        break;

      case "draft":
      default:
        showStateMessage(
          "Poll hasn't started",
          "Please wait for the host to start the poll.",
        );
        break;
    }
  }

  /* ==========================================================
     Live Message
     ========================================================== */

  function showLiveMessage(message) {
    if (!liveMessage) {
      return;
    }

    liveMessage.textContent = message;

    liveMessage.classList.add("visible");

    window.clearTimeout(showLiveMessage.timeout);

    showLiveMessage.timeout = window.setTimeout(() => {
      liveMessage.classList.remove("visible");
    }, 2200);
  }

  /* ==========================================================
     Update Results
     ========================================================== */

  function updateResults(analytics) {
    if (!analytics || !liveResults) {
      return;
    }

    const optionVotes = Array.isArray(analytics.option_votes)
      ? analytics.option_votes
      : [];

    const optionPercentages = Array.isArray(analytics.option_percentages)
      ? analytics.option_percentages
      : [];

    const rows = liveResults.querySelectorAll(".participant-result-row");

    rows.forEach((row) => {
      const index = Number(row.dataset.optionIndex);

      const votes = Number(optionVotes[index] || 0);

      const percentage = Number(optionPercentages[index] || 0);

      const percentageElement = row.querySelector(
        ".participant-result-percentage",
      );

      const progressBar = row.querySelector(".participant-result-progress-bar");

      const votesElement = row.querySelector(".participant-result-votes");

      if (percentageElement) {
        percentageElement.textContent = `${percentage}%`;
      }

      if (progressBar) {
        progressBar.style.width = `${Math.min(Math.max(percentage, 0), 100)}%`;
      }

      if (votesElement) {
        votesElement.textContent = `${votes} ${votes === 1 ? "vote" : "votes"}`;
      }
    });
  }

  /* ==========================================================
     Socket Connection
     ========================================================== */

  if (typeof PollSocket === "undefined") {
    console.error("PollSocket is not available.");

    return;
  }

  PollSocket.connect();

  /* ==========================================================
     Join Poll Room
     ========================================================== */

  PollSocket.joinPoll(pollCode);

  /* ==========================================================
     Poll State
     ========================================================== */

  PollSocket.on("poll_state", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    handlePollState(data.status);
  });

  /* ==========================================================
     Poll Started
     ========================================================== */

  PollSocket.on("poll_started", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    handlePollState("active");

    showLiveMessage("Voting is now open.");
  });

  /* ==========================================================
     Poll Paused
     ========================================================== */

  PollSocket.on("poll_paused", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    handlePollState("paused");

    showLiveMessage("Voting has been paused.");
  });

  /* ==========================================================
     Poll Resumed
     ========================================================== */

  PollSocket.on("poll_resumed", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    handlePollState("active");

    showLiveMessage("Voting has resumed.");
  });

  /* ==========================================================
     Poll Ended
     ========================================================== */

  PollSocket.on("poll_ended", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    handlePollState("ended");

    showLiveMessage("Poll has ended.");
  });

  /* ==========================================================
     Results Updated
     ========================================================== */

  PollSocket.on("results_updated", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    updateResults(data.analytics);
  });

  /* ==========================================================
     Vote Submitted
     ========================================================== */

  PollSocket.on("vote_submitted", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    showLiveMessage("Vote recorded.");
  });

  /* ==========================================================
     Vote Updated
     ========================================================== */

  PollSocket.on("vote_updated", (data) => {
    if (!data || data.poll_code !== pollCode) {
      return;
    }

    showLiveMessage("Vote updated.");
  });

  /* ==========================================================
     Socket Error
     ========================================================== */

  PollSocket.on("socket_error", (data) => {
    if (data && data.message) {
      showLiveMessage(data.message);
    }
  });

  /* ==========================================================
     Initial Status
     ========================================================== */

  const initialStatus = statusText
    ? statusText.textContent.trim().toLowerCase()
    : null;

  if (initialStatus) {
    handlePollState(initialStatus);
  }
});
