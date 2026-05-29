## ADDED Requirements

### Requirement: Agent email status check
The agent SHALL be able to check the user's email bind status.

#### Scenario: Check email bind status
- **WHEN** the agent invokes `check_email_status` tool
- **THEN** the system SHALL return the bind state (bound/unbound), email address, bind time, and last sync time
- **WHEN** the user has not bound an email
- **THEN** the system SHALL indicate that email is not bound

### Requirement: Agent email list query
The agent SHALL be able to query synced emails with optional title keyword filter and result count limit.

#### Scenario: Query email list
- **WHEN** the agent invokes `get_emails` tool without a query filter
- **THEN** the system SHALL return the most recent 20 synced emails with title, sender, release time
- **WHEN** the agent invokes `get_emails` with a `query` parameter (title keyword)
- **THEN** the system SHALL return emails whose title matches the keyword
- **WHEN** the agent invokes `get_emails` with a `max_results` parameter
- **THEN** the system SHALL limit the returned results to the specified count (max 50)
- **WHEN** emails have not been synced yet
- **THEN** the system SHALL return an empty list with a hint to sync first

### Requirement: Agent email sending
The agent SHALL be able to send emails on behalf of the user through the bound email account.

#### Scenario: Send email
- **WHEN** the agent invokes `send_email` tool with `to`, `subject`, and `body` parameters
- **THEN** the system SHALL send the email via `POST /api/v1/email/send`
- **THEN** the system SHALL return success or detailed error message

#### Scenario: Send email error handling
- **WHEN** the agent invokes `send_email` but email is not bound
- **THEN** the system SHALL return an error indicating the email is not bound
- **WHEN** the agent invokes `send_email` with missing parameters
- **THEN** the system SHALL return an error indicating required fields are missing
