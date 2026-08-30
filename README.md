# Real-Time Polling and Analytics System

A real-time web-based polling and analytics application built with **Python, Flask, Flask-SocketIO, HTML, CSS, and JavaScript**.

The system allows a host to create and control live polls while participants join using a poll code and submit votes in real time. Hosts can monitor participation and live analytics without refreshing the page.

---

## Overview

The **Real-Time Polling and Analytics System** demonstrates how a modern interactive polling application can be developed using Flask and real-time WebSocket communication.

A host can create a poll, configure its behavior, start and control the poll, and monitor live responses and analytics.

Participants can join a poll using a unique poll code, submit their responses, and receive real-time poll and result updates.

The application uses **Flask-SocketIO** to synchronize important events between the server, host, and participants.

---

## Features

### Poll Creation

Hosts can create polls with:

- Custom questions
- Multiple options
- Single-choice voting
- Multiple-choice voting
- Anonymous voting configuration
- Vote-change configuration
- Live-result configuration
- Quiz mode
- Correct answers
- Optional time limits

### Real-Time Poll Control

Hosts can control the poll lifecycle:

- Start
- Pause
- Resume
- End

Poll state changes are communicated to connected clients in real time.

Participants do not need to refresh their browsers when the poll state changes.

### Real-Time Voting

Participants can submit their votes while a poll is active.

When a vote is submitted:

1. The server validates the request.
2. The participant's vote is stored.
3. The participant's voting state is updated.
4. Analytics are recalculated.
5. Connected clients receive updated results.

### Multiple Participants

Multiple participants can join the same poll simultaneously.

The host can monitor participation while participants receive synchronized poll updates.

### Live Analytics

The host dashboard provides live analytics including:

- Total participants
- Total votes
- Response rate
- Voting rate
- Leading option
- Vote distribution
- Votes over time

Analytics are recalculated on the server and broadcast to connected clients.

### Vote Changes

Hosts can decide whether participants are allowed to change their votes.

When vote changes are enabled, the existing vote is updated instead of being counted as an additional participant.

When vote changes are disabled, additional voting attempts are rejected by the server.

### Poll Timer

Polls can optionally have a time limit.

The timer supports:

- Countdown
- Pause
- Resume
- Automatic expiration

The current validation rules allow time limits from **5 seconds** to **3600 seconds (1 hour)**.

### Automatic Poll Expiration

When the timer reaches zero, the poll transitions from active to expired and voting is disabled.

Expiration is enforced by the server, not only by the client-side countdown.

### Quiz Mode

Polls can optionally operate as quizzes with:

- Correct answer configuration
- Single-choice quizzes
- Multiple-choice quizzes
- Server-side correct-answer validation

### Server-Side Validation

The server is authoritative for important poll and voting rules.

Validation includes:

- Poll code validation
- Question validation
- Option validation
- Duplicate option detection
- Time-limit validation
- Boolean configuration validation
- Correct-answer validation
- Selected option validation
- Duplicate vote prevention
- Vote-change restrictions
- Poll status validation

### Participant Sessions

Participant sessions are managed using Flask sessions.

Each participant receives a cryptographically secure participant identifier generated using Python's `secrets` module.

### Host Access Protection

The host dashboard is protected using a Flask session-based poll association.

Host Socket.IO operations verify this association before allowing poll lifecycle changes.

### Real-Time Communication

The application uses **Flask-SocketIO** for real-time communication, including:

- Connection status
- Poll state changes
- Poll start, pause, resume, and end
- Poll expiration
- Participant updates
- Vote submission and updates
- Results updates

### Poll Rooms

Each poll has its own Socket.IO room using the pattern:

```text
poll:<POLL_CODE>
```

For example:

```text
poll:ABC123
```

This keeps poll-specific real-time events isolated.

### Responsive UI

The application is designed for desktop, laptop, tablet, and mobile screens.

The Home page also includes a Lottie animation for a more engaging introduction.

---

## Technology Stack

### Backend

- Python
- Flask
- Flask-SocketIO

### Frontend

- HTML5
- CSS3
- JavaScript

### Real-Time Communication

- Socket.IO
- WebSocket-based communication

### State Management

- Thread-safe in-memory state
- Python `RLock`

### Security and Validation

- Python `secrets`
- Server-side validation
- Flask sessions

### Animation

- Lottie
- LottieFiles

---

## Application Architecture

The application follows a layered architecture separating routes, services, models, state management, and real-time events.

### Routes

Responsible for:

- Handling HTTP requests
- Processing form data
- Rendering templates
- Redirecting users
- Connecting requests with application services

### Services

Contain application logic for:

- Poll management
- Poll lifecycle management
- Voting
- Participant sessions
- Analytics
- Security validation

### Models

Represent application entities such as:

- Poll
- Participant

### State Management

Application state is maintained through dedicated state classes.

Poll and participant state are managed independently and coordinated through a central state manager.

### Socket Events

Handle:

- Connection lifecycle
- Poll room membership
- Real-time poll controls
- Voting events
- Participant updates
- Result updates
- Poll expiration

### Frontend

Handles:

- User interaction
- Poll rendering
- Real-time updates
- Analytics visualization
- Countdown display
- Responsive presentation

---

## Poll Lifecycle

A poll follows a controlled lifecycle:

```text
Created
   ↓
Waiting
   ↓
Active
   ├──→ Paused
   │      ↓
   │    Active
   │
   ├──→ Ended
   │
   └──→ Expired
```

### Waiting

The poll has been created but voting has not started.

### Active

Participants can submit votes.

### Paused

Voting is temporarily suspended.

### Ended

The host manually ends the poll.

### Expired

A time-limited poll reaches its server-defined expiration time.

---

## Real-Time Vote Flow

A typical vote submission follows this process:

```text
Participant
    │
    │ Submit Vote
    ▼
Flask Route
    │
    ▼
VoteService
    │
    ├── Validate Participant
    ├── Validate Poll
    ├── Validate Poll State
    ├── Validate Options
    └── Store Vote
    │
    ▼
AnalyticsService
    │
    ▼
Socket.IO
    │
 ┌──┴──────────────┐
 ▼                 ▼
Host           Participants
 │                 │
 ▼                 ▼
Analytics        Results
Update           Update
```

---

## Analytics

Analytics are generated from the current poll state.

### Total Participants

The number of participants associated with the poll.

### Total Votes

The number of participants who have submitted a vote.

### Response Rate

The percentage of participants who have submitted a vote.

### Voting Rate

The rate at which votes are submitted during the poll.

### Leading Option

The option currently receiving the highest number of votes.

### Vote Distribution

The distribution of votes across available options.

### Votes Over Time

A time-based representation of voting activity.

---

## Security

The application uses a server-authoritative security model.

### Secure Participant IDs

Participant identifiers are generated using Python's `secrets` module.

### Poll Code Validation

Poll codes are normalized and validated before being used.

### Vote Validation

Submitted options are validated for:

- Correct data type
- Valid option range
- Duplicate selections
- Single-choice restrictions
- Multiple-choice restrictions

### Duplicate Vote Prevention

Participants cannot submit another vote when vote changes are disabled.

### Vote Change Validation

Vote changes are allowed only when the poll configuration permits them.

### Poll Status Validation

Voting is rejected when the poll is:

- Paused
- Ended
- Expired
- Otherwise inactive

### Host Authorization

Host poll-control events verify the host's session association before changing poll state.

### Participant Authorization

Participant operations verify that the participant belongs to the requested poll.

---

## Time-Limited Polls

A poll can optionally have a time limit.

Supported limits are:

```text
Minimum: 5 seconds
Maximum: 3600 seconds
```

The server maintains the authoritative expiration time.

The client-side countdown is a visual representation of server state rather than the authority for poll expiration.


---

## Usage

### Host

1. Open the application.
2. Select **Create a Poll**.
3. Enter the poll question.
4. Add poll options.
5. Configure the available settings.
6. Create the poll.
7. Share the generated poll code with participants.
8. Start the poll.
9. Monitor votes and analytics in real time.
10. Pause, resume, or end the poll when required.

### Participant

1. Select **Join a Poll**.
2. Enter the poll code.
3. Join the poll.
4. Wait for the host to start the poll.
5. Submit a response.
6. View live results when available.
7. Change the response if the host allows vote changes.

---

## Error Handling

The application handles invalid operations through server-side validation and user-facing error messages.

Examples include:

- Invalid poll code
- Poll not found
- Invalid question
- Invalid options
- Duplicate options
- Invalid time limit
- Invalid option selection
- Duplicate voting
- Unauthorized poll control
- Voting while paused
- Voting after poll end
- Voting after expiration
- Invalid participant session

---

## Current State Management

The current implementation uses **thread-safe in-memory state** for active polls and participants.

This approach is suitable for:

- Local development
- Demonstrations
- Learning real-time application architecture
- Small-scale testing

Application state exists only while the application process is running.

Restarting the application clears the in-memory poll and participant state.


---

## Testing

The application has been tested across the primary user flows.

Tested functionality includes:

- Poll creation
- Participant joining
- Real-time poll start
- Real-time voting
- Multiple participants
- Vote changes
- Poll pause
- Poll resume
- Manual poll ending
- Automatic poll expiration
- Server-side vote validation
- Invalid input handling
- Host authorization
- Participant session handling
- Real-time analytics
- Countdown behavior
- Responsive Home page
- Responsive polling interface
- Responsive host dashboard

---

## Design Goals

The project focuses on demonstrating practical full-stack and real-time web development concepts.

Key goals include:

- Clean separation of application responsibilities
- Server-side validation
- Real-time client synchronization
- Event-driven application behavior
- Thread-safe state management
- Interactive analytics
- Responsive frontend development
- Secure participant identification
- Controlled poll lifecycle management

---

## Learning Outcomes

This project provides practical experience with:

- Python backend development
- Flask application development
- Flask routing
- Flask sessions
- Service-layer architecture
- Object-oriented Python
- WebSocket communication
- Socket.IO rooms and events
- Client-server synchronization
- Server-side validation
- Security-aware backend development
- Thread-safe state management
- Real-time analytics
- JavaScript event handling
- Responsive CSS
- Lottie animation integration



---

## Project Scope

The project is designed as a complete real-time polling application demonstrating the interaction between a Python backend, browser-based frontend, server-side application logic, and real-time Socket.IO communication.

The current implementation prioritizes:

**Real-time functionality → Server-side validation → Clean architecture → Responsive UI → Maintainability**

The application is suitable as a learning project, portfolio project, and demonstration of practical full-stack development concepts.
