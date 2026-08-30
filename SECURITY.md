# Security Documentation

## Real-Time Polling and Analytics System

This document describes the security concepts, controls, validation rules, authorization checks, and security-related design decisions implemented in the Real-Time Polling and Analytics System.

The project follows a **server-authoritative security model**: the browser can request an operation, but the server validates the request and decides whether the operation is allowed.

---

## 1. Security Goals

The main security goals of the application are:

- Prevent invalid poll access.
- Prevent unauthorized poll control.
- Prevent unauthorized participant actions.
- Prevent duplicate voting.
- Enforce vote-change rules.
- Validate all submitted voting options.
- Prevent voting on inactive polls.
- Enforce poll expiration on the server.
- Generate secure participant identifiers.
- Protect shared application state from concurrent modification.
- Keep poll-specific real-time events isolated.

---

## 2. Server-Authoritative Security

The server is the final authority for important application rules.

Client-side JavaScript and HTML controls are treated as user-interface features, not security boundaries.

The basic model is:

```text
Browser
   ↓
User Input
   ↓
Server
   ↓
Validation
   ↓
Authorization
   ↓
Business Logic
   ↓
State Change
```

For example, disabling a voting button in the browser does not prevent a malicious client from sending a request manually.

Therefore, the server performs the actual validation before accepting the vote.

---

## 3. Participant Identity

Participants receive a unique participant identifier when they join a poll.

The identifier is generated using Python's `secrets` module.

The project uses:

```python
secrets.token_urlsafe(...)
```

This provides cryptographically secure random values suitable for security-sensitive identifiers.

The participant ID is then associated with the participant's Flask session.

---

## 4. Flask Sessions

Flask sessions are used to associate the current browser session with an application identity.

The participant session stores the participant ID.

Conceptually:

```text
Browser Session
      ↓
participant_id
      ↓
Participant
      ↓
Poll
```

This allows the server to determine which participant is making a request.

---

## 5. Participant-Poll Authorization

A participant must belong to the poll they are attempting to access.

The application verifies that:

```text
participant.poll_code == poll.code
```

If the participant belongs to a different poll, the operation is rejected.

This prevents a participant session associated with one poll from being used to perform participant operations against another poll.

---

## 6. Host Authorization

Host operations require verification that the current host session is associated with the requested poll.

The host session is associated with the poll created by that browser session.

Before sensitive host operations are performed, the server verifies the session-to-poll relationship.

This protects operations such as:

- Start
- Pause
- Resume
- End
- Other host-controlled poll actions

---

## 7. Poll Code Validation

Poll codes are validated before being used.

The application uses the following pattern:

```text
^[A-Z0-9]{6}$
```

This means a valid poll code contains:

- Exactly 6 characters
- Uppercase letters
- Digits
- No additional characters

Input is normalized using:

```python
poll_code.strip().upper()
```

This provides consistent handling of participant-entered poll codes.

---

## 8. Input Validation

The server validates user-supplied input before using it.

Validation is applied to:

- Questions
- Poll options
- Poll codes
- Time limits
- Boolean configuration values
- Quiz correct answers
- Submitted voting options

Validation is centralized in reusable validation functions and security-related service methods.

---

## 9. Question Validation

Poll questions are validated to ensure:

- The value is text.
- The value is not empty.
- Leading and trailing whitespace is removed.
- The question does not exceed the configured maximum length.

The default maximum question length is:

```text
500 characters
```

---

## 10. Poll Option Validation

Poll options are validated to ensure:

- Options are provided as a list.
- At least two options exist.
- No more than ten options exist.
- Each option is text.
- Options are not empty.
- Each option does not exceed the configured maximum length.
- Duplicate options are rejected.

Option comparison uses case-insensitive normalization through:

```python
casefold()
```

This prevents logically duplicate options such as:

```text
Python
python
PYTHON
```

---

## 11. Time-Limit Validation

Time limits are validated on the server.

The supported limits are:

```text
Minimum: 5 seconds
Maximum: 3600 seconds
```

The validation also rejects invalid types.

Boolean values are specifically prevented from being accepted as integer time limits.

---

## 12. Boolean Configuration Validation

Boolean configuration values are explicitly validated.

For example, settings such as:

- Multiple choice
- Quiz mode
- Anonymous voting
- Vote changes
- Live results

must contain actual Boolean values rather than arbitrary values.

---

## 13. Vote Validation

Every submitted vote is validated before being stored.

The server verifies:

- The selected options are provided as a list.
- At least one option is selected.
- Single-choice polls contain exactly one selection.
- Multiple selections are not duplicated.
- Every option index is an integer.
- Every option index is within the valid range.

---

## 14. Option Index Validation

For a poll with `N` options, valid indexes are:

```text
0 ... N-1
```

Any negative index or index greater than or equal to the number of options is rejected.

For example, if a poll contains four options:

```text
0
1
2
3
```

then:

```text
4
-1
```

are invalid.

---

## 15. Duplicate Selection Prevention

The server rejects duplicate option indexes.

For example:

```text
[1, 1]
```

is invalid.

This prevents malformed multiple-choice submissions.

---

## 16. Single-Choice Enforcement

If a poll is configured as single-choice, the server requires exactly one selected option.

For example:

```text
[2]
```

is valid.

But:

```text
[1, 2]
```

is rejected.

This rule is enforced server-side.

---

## 17. Multiple-Choice Enforcement

Multiple-choice polls may contain multiple selected options.

However, the selected indexes must still:

- Be valid integers.
- Be within range.
- Be unique.

---

## 18. Duplicate Vote Prevention

The application prevents participants from submitting multiple independent votes when vote changes are disabled.

The server checks whether the participant already has a vote.

If a vote already exists and changes are not allowed, the server raises an error.

Example:

```text
First vote:
Participant → Option A

Second vote:
Rejected
```

---

## 19. Vote Change Security

Vote changes are controlled by the poll configuration.

If:

```text
allow_vote_changes = False
```

then the existing vote cannot be replaced.

If:

```text
allow_vote_changes = True
```

then the participant can replace the existing vote.

The server validates this rule rather than trusting the frontend.

---

## 20. Vote Count Integrity

Changing a vote does not create another participant vote.

Example:

```text
Before:
Option A → 1
Total Votes → 1

Participant changes to Option B

After:
Option A → 0
Option B → 1
Total Votes → 1
```

This preserves vote-count integrity.

---

## 21. Poll Status Validation

The server checks poll status before accepting votes.

Voting is accepted only when the poll is active.

Voting is rejected when the poll is:

- Paused
- Ended
- Expired
- Otherwise inactive

---

## 22. Paused Poll Protection

When a poll is paused, participants cannot submit votes.

The server returns an appropriate validation error.

The browser may also disable voting controls, but the server-side restriction is the actual security control.

---

## 23. Ended Poll Protection

After the host manually ends a poll, the server rejects new voting attempts.

The poll remains available for viewing final results, but voting is no longer permitted.

---

## 24. Expired Poll Protection

Time-limited polls are checked against their server-side expiration time.

The server compares the current time with the poll's expiration time.

Conceptually:

```text
Current Time >= End Time
        ↓
Poll becomes Expired
        ↓
Voting rejected
```

This prevents a participant from bypassing the client-side countdown.

---

## 25. Client Timer Is Not the Security Boundary

The countdown shown in the browser is primarily a user-interface feature.

A user could potentially modify or disable client-side JavaScript.

Therefore:

```text
Client Timer
     ≠
Security Authority
```

The server's expiration check is authoritative.

---

## 26. Server-Side Expiration

When the server detects that a poll has reached its expiration time, it updates the poll state to:

```text
expired
```

It also records the ending time.

Any subsequent vote attempt is rejected.

---

## 27. Quiz Correct-Answer Validation

Correct answers are validated only when quiz mode is enabled.

The server verifies:

- Correct answers are provided in quiz mode.
- At least one correct answer exists.
- Single-choice quizzes have one correct answer.
- Duplicate correct answers are rejected.
- Correct answer indexes are integers.
- Correct answer indexes are within range.

---

## 28. Poll Code Normalization

Poll codes are normalized before lookup.

For example:

```text
 abc123
```

becomes:

```text
ABC123
```

This prevents unnecessary failures caused by:

- Leading whitespace
- Trailing whitespace
- Lowercase input

---

## 29. Error Handling

Security and validation failures are converted into controlled application errors.

Examples include:

```text
Poll not found.
Invalid poll code.
Invalid option selected.
You have already voted.
Vote changes are not allowed for this poll.
Voting is temporarily paused.
This poll has ended.
This poll has expired.
Participant does not belong to this poll.
```

The application avoids silently accepting invalid operations.

---

## 30. Authorization vs Validation

These are separate security concepts.

### Validation

Checks whether the supplied data is valid.

Example:

```text
Is option index 3 valid?
```

### Authorization

Checks whether the user is allowed to perform the operation.

Example:

```text
Does this participant belong to this poll?
```

Both are required.

---

## 31. Authentication vs Authorization

### Authentication

Answers:

> Who is this user?

### Authorization

Answers:

> What is this user allowed to do?

The current project uses session-based participant and host associations rather than a full user-account authentication system.

---

## 32. Socket.IO Security

Real-time operations also require server-side authorization.

A Socket.IO client cannot be considered trusted simply because it successfully established a connection.

Sensitive real-time actions must validate the associated session and poll.

The server must determine whether the client is authorized to perform the requested operation.

---

## 33. Socket.IO Room Isolation

Each poll has its own Socket.IO room.

The naming pattern is:

```text
poll:<POLL_CODE>
```

Example:

```text
poll:ABC123
```

Events are broadcast to the appropriate poll room.

This provides logical isolation between different polls.

---

## 34. Real-Time Event Integrity

Important state changes are performed on the server before corresponding real-time events are broadcast.

The general sequence is:

```text
Client Request
      ↓
Server Validation
      ↓
State Change
      ↓
Analytics Update
      ↓
Socket Event
      ↓
Connected Clients
```

The server does not treat a client-side event as proof that a state change is valid.

---

## 35. Shared State Protection

The application uses in-memory state.

Because multiple requests and real-time operations can access shared state, the state-management layer uses synchronization.

A Python `RLock` protects shared operations.

This reduces the risk of concurrent modifications producing inconsistent state.

---

## 36. Reentrant Lock (`RLock`)

`RLock` is a reentrant synchronization primitive provided by Python.

It is useful when protected methods may call other protected methods within the same thread.

The state manager uses locking around operations such as:

- Add
- Get
- Remove
- Exists
- Count
- Retrieve all

---

## 37. Secure Randomness

The application uses the Python `secrets` module for participant identifiers.

This is more appropriate for security-sensitive random identifiers than general-purpose pseudo-random generation.

Example:

```python
secrets.token_urlsafe(16)
```

---

## 38. Trust Boundary

The browser is considered an untrusted environment.

The trust boundary is:

```text
                 TRUST BOUNDARY
                       │
Browser ──────────────→│ Server
                       │
                       ▼
                Validation
                       │
                       ▼
                Authorization
                       │
                       ▼
                  State Change
```

Anything submitted by the browser should be validated by the server.

---

## 39. Defense in Depth

The project uses multiple layers of protection.

For example, voting protection can involve:

```text
UI Restriction
      +
Session Check
      +
Poll Membership Check
      +
Poll Status Check
      +
Vote Validation
      +
Duplicate Vote Check
      +
Server-Side State Update
```

The UI is useful for user experience, but server-side controls provide the actual enforcement.

---

## 40. Data Integrity

The application protects the integrity of poll data by:

- Validating input
- Preventing duplicate votes
- Enforcing poll states
- Validating participant ownership
- Controlling vote changes
- Synchronizing shared state
- Updating analytics after valid state changes

---

## 41. Current Security Scope

The current implementation focuses on application-level security appropriate for the project's scope.

Implemented areas include:

- Secure participant identifiers
- Session-based identity
- Host authorization
- Participant authorization
- Server-side validation
- Vote integrity
- Poll-state enforcement
- Server-side expiration
- Socket.IO room isolation
- Thread-safe shared state

---

## 42. Production Security Considerations

For a production deployment, additional security controls should be considered.

Potential additions include:

- HTTPS
- Secure cookie configuration
- `HttpOnly` cookies
- `SameSite` cookie policy
- CSRF protection for state-changing HTTP requests
- Rate limiting
- Request-size limits
- Strong production secret keys
- Security headers
- Content Security Policy
- Structured security logging
- Monitoring and alerting
- Abuse detection
- Persistent authentication
- Role-based access control
- Database access controls
- Redis security configuration
- Input/output auditing

These are outside the current application's implementation scope unless explicitly added.

---

## 43. Production Secret Key

A production Flask application should use a strong secret key supplied through a secure environment variable or secret-management system.

The secret key should not be committed to source control.

A production configuration should use environment-based configuration rather than hard-coded secrets.

---

## 44. HTTPS

Production deployments should use HTTPS.

HTTPS protects communication between the browser and server against network-level interception and tampering.

The intended production flow is:

```text
Browser
   ⇅ HTTPS
Server
```

rather than transmitting application traffic over plain HTTP.

---

## 45. Secure Cookies

In production, session cookies should be configured with appropriate security attributes.

Important considerations include:

- `Secure`
- `HttpOnly`
- `SameSite`

These settings reduce the risk of session-cookie exposure and certain browser-based attacks.

---

## 46. CSRF Protection

State-changing HTTP requests can require CSRF protection in a production application.

Relevant operations include:

- Creating polls
- Starting polls
- Pausing polls
- Resuming polls
- Ending polls
- Submitting votes

CSRF protection is an additional production hardening measure.

---

## 47. Rate Limiting

Rate limiting can help prevent abuse such as:

- Excessive poll creation
- Repeated join attempts
- Excessive vote submissions
- Automated requests
- Resource exhaustion

The current project does not require a dedicated rate-limiting system for its demonstration scope.

---

## 48. Persistent Storage Security

The current project uses in-memory state.

If a database is introduced, additional controls should be considered:

- Database credentials stored securely
- Parameterized queries or ORM usage
- Least-privilege database users
- Connection security
- Backup protection
- Sensitive data minimization

---

## 49. Distributed Real-Time Security

If the application is scaled across multiple servers, shared infrastructure such as Redis may be introduced.

The production architecture would need to protect:

- Redis connections
- Authentication credentials
- Network access
- Pub/sub communication
- Shared state

The same server-authoritative authorization model should continue to apply.

---

## 50. Security Principles Demonstrated

The project demonstrates several important security principles:

### Never Trust Client Input

All important client-supplied values are validated server-side.

### Least Privilege

Participants receive participant-level capabilities rather than host-level control.

### Defense in Depth

Multiple validation and authorization checks protect sensitive operations.

### Secure Randomness

Security-sensitive identifiers are generated using `secrets`.

### Server Authority

The server determines whether an operation is valid.

### State Integrity

Poll and participant state is protected from invalid and conflicting updates.

### Separation of Responsibilities

Security-related validation is separated into dedicated services and validators.

---

## 51. Security Flow for Voting

The complete voting security flow is:

```text
Participant
     │
     ▼
Submit Vote
     │
     ▼
Session Check
     │
     ▼
Participant Lookup
     │
     ▼
Poll Lookup
     │
     ▼
Participant-Poll Authorization
     │
     ▼
Poll Status Validation
     │
     ▼
Vote-Change / Duplicate Vote Check
     │
     ▼
Option Validation
     │
     ▼
Store Vote
     │
     ▼
Recalculate Analytics
     │
     ▼
Broadcast Results
```

Only after the required checks succeed is the vote accepted.

---

## 52. Security Flow for Host Actions

Host-controlled operations follow the principle:

```text
Host Request
     │
     ▼
Session Check
     │
     ▼
Associated Poll Lookup
     │
     ▼
Authorization Check
     │
     ▼
Poll State Validation
     │
     ▼
Apply State Change
     │
     ▼
Broadcast Event
```

This prevents normal clients from directly controlling another host's poll.

---

## 53. Security Summary

The application's security model can be summarized as:

```text
Untrusted Client
       ↓
Session Verification
       ↓
Input Validation
       ↓
Authorization
       ↓
Poll State Validation
       ↓
Business Rule Validation
       ↓
Thread-Safe State Update
       ↓
Real-Time Broadcast
```

The central security principle is:

> **The client requests an action; the server decides whether that action is allowed.**

---

## 54. Important Interview Points

When explaining the project's security in an interview, the most important points are:

1. The server is authoritative.
2. Client-side restrictions are not treated as security controls.
3. Participant IDs are generated using Python's `secrets` module.
4. Flask sessions associate browsers with participants and hosts.
5. Participants are checked against their poll.
6. Host actions are authorized against the host session.
7. Votes are validated on the server.
8. Duplicate votes are prevented.
9. Vote changes follow poll configuration.
10. Poll status is checked before accepting votes.
11. Poll expiration is enforced server-side.
12. Socket.IO rooms isolate poll events.
13. Shared in-memory state is protected using `RLock`.
14. Production deployment would require additional controls such as HTTPS, secure cookies, CSRF protection, rate limiting, and persistent authentication.

---

## Final Security Model

The project's security architecture follows this principle:

```text
            CLIENT
              │
              │ Untrusted Request
              ▼
        ┌───────────────┐
        │     Flask     │
        │     Route     │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │    Session    │
        │ Verification  │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │    Input      │
        │  Validation    │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Authorization │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Business Rule │
        │  Validation   │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Thread-Safe   │
        │ State Change  │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │   Socket.IO   │
        │   Broadcast   │
        └───────┬───────┘
                ▼
             CLIENTS
```

The application therefore follows a **defense-in-depth, server-authoritative approach** appropriate for a real-time polling application.
