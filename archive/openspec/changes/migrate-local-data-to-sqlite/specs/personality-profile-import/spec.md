## ADDED Requirements

### Requirement: Personality profile import

The system SHALL import JSON personality profile files from `personality/profiles/` into the `user_match_profile` table.

#### Scenario: Import a valid profile
- **WHEN** a `<user_id>.json` file exists in `personality/profiles/` containing a valid JSON object with profile data (interests, skills, MBTI, preferences)
- **THEN** the system extracts `user_id` from the filename, serializes the entire profile object as JSON text into the `answers` column, and upserts into `user_match_profile` with `is_open = 0`

#### Scenario: Preserve last_updated as last_match_time
- **WHEN** the profile JSON contains a `last_updated` field
- **THEN** the system stores its value in `last_match_time`

#### Scenario: Skip if user does not exist
- **WHEN** the extracted `user_id` does not exist in the `users` table
- **THEN** the system logs a warning and skips that profile

#### Scenario: Idempotent upsert
- **WHEN** a `user_match_profile` row already exists for the same `user_id`
- **THEN** the system updates the existing row with the new profile data (upsert behavior)
