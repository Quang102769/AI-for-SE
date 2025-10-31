# Comprehensive Unit Test Design - TimeWeave Meeting Scheduler

## Test Cases Overview

This document provides comprehensive unit test cases for all functions and methods in the TimeWeave Meeting Scheduler application.

---

## 1. UTILITY FUNCTIONS (src/meetings/utils.py)

### 1.1 generate_time_slots()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Generate slots for single day | meeting_request with date_range_start='2024-01-01', date_range_end='2024-01-01', work_hours_start='09:00', work_hours_end='17:00', duration_minutes=60, step_size_minutes=30, timezone='UTC' | List of tuples with slots: [(2024-01-01 09:00 UTC, 2024-01-01 10:00 UTC), (2024-01-01 09:30 UTC, 2024-01-01 10:30 UTC), ...] up to 16:00-17:00 |
| Basic Functionality | Generate slots for multiple days | meeting_request with date_range='2024-01-01' to '2024-01-03', work_hours='09:00-17:00', duration=60, step=30, work_days_only=False | List of tuples spanning 3 days with proper slot distribution |
| Edge Case | Date range with weekends (work_days_only=True) | date_range='2024-01-05' (Fri) to '2024-01-08' (Mon), work_days_only=True | Slots only for Friday and Monday, Saturday and Sunday excluded |
| Edge Case | Date range with weekends (work_days_only=False) | date_range='2024-01-05' (Fri) to '2024-01-08' (Mon), work_days_only=False | Slots for all 4 days including weekend |
| Edge Case | Duration exceeds work hours | work_hours='09:00-17:00' (8 hours), duration_minutes=540 (9 hours) | Empty list (no slots can fit) |
| Edge Case | Duration exactly equals available time | work_hours='09:00-17:00', duration=480 (8 hours), step=60 | Single slot: [(09:00, 17:00)] |
| Edge Case | Step size larger than duration | duration_minutes=30, step_size_minutes=60 | Slots generated with 60-minute intervals, each lasting 30 minutes |
| Edge Case | Slot ends exactly at work_hours_end | work_hours_end='17:00', last possible slot ends at '17:00' | Include slot that ends exactly at 17:00 |
| Timezone | Non-UTC timezone conversion | timezone='Asia/Ho_Chi_Minh' (UTC+7), work_hours='09:00-17:00' local | All returned datetimes in UTC (02:00-10:00 UTC) |
| Timezone | DST boundary crossing | Date range crossing DST change, timezone='America/New_York' | Correct UTC conversion handling DST offset changes |
| Error Handling | Invalid timezone string | timezone='Invalid/Timezone' | Should raise exception or handle gracefully |
| Performance | Long date range | date_range spanning 90 days with 15-minute steps | Function completes within reasonable time, returns all valid slots |

### 1.2 is_participant_available()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Participant with no busy slots | participant with no BusySlot records, any time range | True |
| Basic Functionality | Participant with non-overlapping busy slots | participant has busy: 09:00-10:00, check: 14:00-15:00 | True |
| Edge Case | Busy slot starts when check ends | busy: 10:00-11:00, check: 09:00-10:00 | True (no overlap) |
| Edge Case | Busy slot ends when check starts | busy: 09:00-10:00, check: 10:00-11:00 | True (no overlap) |
| Edge Case | Busy slot completely contains check slot | busy: 09:00-12:00, check: 10:00-11:00 | False |
| Edge Case | Check slot completely contains busy slot | busy: 10:00-11:00, check: 09:00-12:00 | False |
| Edge Case | Partial overlap at start | busy: 09:00-10:30, check: 10:00-11:00 | False |
| Edge Case | Partial overlap at end | busy: 10:30-12:00, check: 10:00-11:00 | False |
| Edge Case | Multiple overlapping busy slots | participant has busy: [09:00-10:00, 14:00-15:00], check: 09:30-10:30 | False (overlaps with first slot) |
| Edge Case | Participant has_responded=False | participant.has_responded=False, check any time | Should still check availability based on busy slots |
| Timezone | UTC time handling | All times in UTC timezone-aware datetimes | Correct overlap detection |

### 1.3 calculate_slot_availability()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | All participants available | meeting_request with 5 participants, all available for time slot | (5, 5, [id1, id2, id3, id4, id5]) |
| Basic Functionality | No participants available | meeting_request with 5 participants, all busy for time slot | (0, 5, []) |
| Basic Functionality | Some participants available | meeting_request with 5 participants, 3 available, 2 busy | (3, 5, [id1, id2, id3]) |
| Edge Case | No participants in meeting | meeting_request.participants.count() = 0 | (0, 0, []) |
| Edge Case | Participants but none responded | meeting_request has 5 participants, all have has_responded=False | (0, 0, []) |
| Edge Case | Only some participants responded | 5 participants total, 3 responded (2 available, 1 busy), 2 not responded | (2, 3, [id1, id2]) |
| Integration | Complex overlapping scenarios | Multiple participants with various overlapping busy slots | Correct count of available participants |

### 1.4 generate_suggested_slots()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | First time generation | meeting_request with no existing SuggestedSlot records, force_recalculate=False | Creates new SuggestedSlot objects for all possible time slots |
| Basic Functionality | Regeneration with force | meeting_request with existing slots, force_recalculate=True | Deletes old slots, creates new ones |
| Basic Functionality | Regeneration without force | meeting_request with existing slots, force_recalculate=False | Updates existing slots using update_or_create |
| Edge Case | No possible slots | All participants busy for all time slots | Empty list or slots with 0 availability |
| Edge Case | All slots 100% available | All participants available for all time slots | All SuggestedSlot objects with available_count = total_participants |
| Edge Case | Meeting config changed | Existing slots don't match new config, force_recalculate=False | Should handle update correctly |
| Integration | Database operations | Various scenarios | Correct use of update_or_create, proper slot data stored |
| Performance | Large number of slots | 90-day range with 15-minute steps | Function completes, all slots generated and stored |

### 1.5 get_top_suggestions()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Standard retrieval | meeting_request with 20 slots, limit=10, min_availability_pct=50 | Returns top 10 slots with ≥50% availability, sorted by availability desc, then start_time asc |
| Edge Case | No slots meet threshold | All slots <50% available, min_availability_pct=50 | Empty list |
| Edge Case | Fewer slots than limit | Only 5 slots available, limit=10 | Returns all 5 slots |
| Edge Case | Exactly limit slots | Exactly 10 slots meet criteria, limit=10 | Returns all 10 slots |
| Edge Case | More slots than limit | 15 slots meet criteria, limit=10 | Returns exactly 10 slots |
| Edge Case | All slots same availability | 10 slots all with 80% availability | Returns 10 slots sorted by start_time ascending |
| Edge Case | min_availability_pct = 0 | min_availability_pct=0 | Returns all slots (none filtered out) |
| Edge Case | min_availability_pct = 100 | min_availability_pct=100 | Returns only slots with 100% availability |
| Edge Case | limit = 0 | limit=0 | Returns empty list |
| Edge Case | Negative limit | limit=-5 | Returns empty list or handles gracefully |
| Sorting | Mixed availability | Slots with availability: [100%, 80%, 80%, 60%] at different times | Correct ordering: 100% first, then 80% slots by time, then 60% |

### 1.6 get_heatmap_data()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | With existing SuggestedSlots | meeting_request with slots, participant_timezone='Asia/Ho_Chi_Minh' | Dict with dates, time_slots, heatmap data in Asia/Ho_Chi_Minh timezone |
| Basic Functionality | Without existing SuggestedSlots | meeting_request with no slots, generates from config | Dict with generated slot data |
| Timezone | UTC timezone | participant_timezone='UTC' | All times displayed in UTC |
| Timezone | Eastern timezone | participant_timezone='America/New_York' | Correct conversion to EST/EDT |
| Timezone | Asian timezone | participant_timezone='Asia/Tokyo' | Correct conversion to JST |
| Timezone | DST boundary | Date range crossing DST, timezone with DST | Correct time display across DST change |
| Edge Case | Single date multiple times | Date range = 1 day, multiple time slots | dates=['2024-01-01'], multiple time_slots |
| Edge Case | Multiple dates single time | Date range multiple days, only one slot per day | Multiple dates, single time_slot |
| Edge Case | Empty date range | No valid slots/dates | Empty or minimal data structure |
| Error Handling | Invalid timezone | participant_timezone='Invalid/Timezone' | Handle gracefully or use default |
| Data Structure | Heatmap levels | Various availability percentages | Correct level (0-5) for each slot |
| Data Structure | Percentage calculation | available=3, total=5 | percentage=60.0 |

### 1.7 format_datetime_for_timezone()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Naive datetime to UTC | dt=datetime(2024, 1, 1, 9, 0) (naive), timezone_str='UTC' | '2024-01-01 09:00' |
| Basic Functionality | Timezone-aware to different timezone | dt=datetime(2024, 1, 1, 9, 0, tzinfo=UTC), timezone_str='Asia/Ho_Chi_Minh' | '2024-01-01 16:00' |
| Timezone | UTC timezone | dt in UTC, timezone_str='UTC' | Correct UTC time string |
| Timezone | EST timezone | dt in UTC, timezone_str='America/New_York' | Correct EST/EDT time string |
| Timezone | JST timezone | dt in UTC, timezone_str='Asia/Tokyo' | Correct JST time string |
| Edge Case | DST boundary time | dt at DST transition, timezone with DST | Correct time with proper offset |
| Error Handling | Invalid timezone string | timezone_str='Invalid/Zone' | Raise exception or handle gracefully |

### 1.8 parse_busy_slots_from_json()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Standard JSON input | json_data=[{'start': '2024-01-01T09:00', 'end': '2024-01-01T10:00'}], participant_timezone='Asia/Ho_Chi_Minh' | [(datetime(2024, 1, 1, 2, 0, tzinfo=UTC), datetime(2024, 1, 1, 3, 0, tzinfo=UTC))] |
| Basic Functionality | Multiple slots | json_data with 3 slots | List of 3 tuples with UTC times |
| Edge Case | Empty list | json_data=[] | [] |
| Edge Case | Single slot | json_data with 1 slot | List with 1 tuple |
| Format | Naive datetime strings | 'start': '2024-01-01T09:00' (no timezone) | Assumes participant timezone, converts to UTC |
| Format | ISO with Z suffix | 'start': '2024-01-01T09:00Z' | Treats as UTC |
| Format | ISO with timezone offset | 'start': '2024-01-01T09:00+07:00' | Parses offset, converts to UTC |
| Error Handling | Missing 'start' key | {'end': '2024-01-01T10:00'} | Raise KeyError or handle gracefully |
| Error Handling | Missing 'end' key | {'start': '2024-01-01T09:00'} | Raise KeyError or handle gracefully |
| Error Handling | Invalid datetime format | 'start': 'invalid-date' | Raise ValueError or handle gracefully |
| Error Handling | Empty strings | 'start': '', 'end': '' | Handle gracefully |
| Error Handling | Invalid timezone | participant_timezone='Invalid/Zone' | Raise exception or handle gracefully |

---

## 2. MODEL METHODS (src/meetings/models.py)

### 2.1 MeetingRequest.save()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | First save | New MeetingRequest instance, no token | Token generated, saved to database |
| Basic Functionality | Subsequent save | Existing MeetingRequest with token, update title | Token unchanged, title updated |
| Edge Case | Token collision | Mock token_urlsafe to return duplicate token | Handle collision (retry or unique constraint) |

### 2.2 MeetingRequest.is_active (property)

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Active with no deadline | status='active', response_deadline=None | True |
| Basic Functionality | Active with future deadline | status='active', response_deadline=tomorrow | True |
| Edge Case | Active with past deadline | status='active', response_deadline=yesterday | False |
| Edge Case | Status locked | status='locked', response_deadline=future | False |
| Edge Case | Status cancelled | status='cancelled', response_deadline=future | False |
| Edge Case | Status draft | status='draft', response_deadline=future | False |

### 2.3 MeetingRequest.response_rate (property)

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Edge Case | No participants | participants.count()=0 | 0 |
| Basic Functionality | All responded | 5 participants, all has_responded=True | 100 |
| Basic Functionality | None responded | 5 participants, all has_responded=False | 0 |
| Basic Functionality | Some responded | 5 participants, 3 responded | 60 |
| Edge Case | Rounding | 3 participants, 1 responded (33.333%) | 33 |

### 2.4 MeetingRequest.get_share_url()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Valid UUID and token | id=valid-uuid, token='abc123' | '/r/{uuid}?t=abc123' |
| Edge Case | Special characters in token | token with special URL characters | Properly URL-encoded |

### 2.5 Participant.__str__()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | With name and email | name='John', email='john@example.com', meeting.title='Team Sync' | 'John (john@example.com) - Team Sync' |
| Edge Case | Only name | name='John', email=None | 'John - Team Sync' |
| Edge Case | Only email | name=None, email='john@example.com' | 'john@example.com - Team Sync' |
| Edge Case | Neither name nor email | name=None, email=None | 'Anonymous - Team Sync' or similar |

### 2.6 BusySlot.clean()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Valid time range | start_time < end_time | No exception |
| Edge Case | Start equals end | start_time = end_time | Raises ValidationError |
| Edge Case | Start after end | start_time > end_time | Raises ValidationError |

### 2.7 SuggestedSlot.availability_percentage (property)

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Edge Case | No participants | total_participants=0 | 0.0 |
| Basic Functionality | None available | available_count=0, total_participants=5 | 0.0 |
| Basic Functionality | All available | available_count=5, total_participants=5 | 100.0 |
| Edge Case | Rounding case | available_count=2, total_participants=3 (66.666%) | 66.7 |
| Edge Case | Another rounding | available_count=1, total_participants=3 (33.333%) | 33.3 |

### 2.8 SuggestedSlot.heatmap_level (property)

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Edge Case | 0% availability | availability_percentage=0.0 | 0 |
| Edge Case | 0.1% availability | availability_percentage=0.1 | 1 |
| Edge Case | 19.9% availability | availability_percentage=19.9 | 1 |
| Boundary | 20% exactly | availability_percentage=20.0 | 2 |
| Boundary | 39.9% availability | availability_percentage=39.9 | 2 |
| Boundary | 40% exactly | availability_percentage=40.0 | 3 |
| Boundary | 59.9% availability | availability_percentage=59.9 | 3 |
| Boundary | 60% exactly | availability_percentage=60.0 | 4 |
| Boundary | 79.9% availability | availability_percentage=79.9 | 4 |
| Boundary | 80% exactly | availability_percentage=80.0 | 5 |
| Basic Functionality | 100% availability | availability_percentage=100.0 | 5 |

---

## 3. EMAIL UTILITY FUNCTIONS (src/meetings/email_utils.py)

### 3.1 send_email_via_resend()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Single recipient valid email | to_email='user@example.com', subject='Test', html_content='<p>Test</p>' | True, email sent via Resend API |
| Basic Functionality | Multiple recipients | to_email=['user1@example.com', 'user2@example.com'], subject, html | True, email sent to all recipients |
| Edge Case | API key not configured | RESEND_API_KEY=None | False, logs to console in development |
| Edge Case | Invalid email format | to_email='invalid-email' | False or Resend API error |
| Error Handling | Resend API error | Mock Resend to raise exception | False, error logged |
| Error Handling | Network timeout | Mock network timeout | False, timeout handled |
| Edge Case | Empty subject | subject='' | Email sent with empty subject or validation error |
| Edge Case | Empty content | html_content='' | Email sent with empty body or validation error |
| Basic Functionality | Custom from_email | from_email='custom@example.com' | Email sent with custom sender |

### 3.2 send_verification_email()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Valid user | user with email, valid verification_url | True, verification email sent |
| Edge Case | User without email | user.email=None or '' | False or error |
| Edge Case | Invalid URL | verification_url=malformed URL | Email sent with malformed URL or error |
| Error Handling | Template rendering error | Mock render_to_string to raise exception | False, error handled |
| Integration | send_email_via_resend fails | Mock send_email_via_resend to return False | False |

### 3.3 send_meeting_invitation_email()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Participant with email | participant.email='user@example.com', valid meeting_request, respond_url | True, invitation sent |
| Edge Case | Participant without email | participant.email=None | False immediately (no API call) |
| Edge Case | Invalid respond_url | respond_url=malformed | Email sent with malformed URL or error |
| Error Handling | Template rendering error | Mock render_to_string to raise exception | False, error handled |
| Integration | send_email_via_resend fails | Mock send_email_via_resend to return False | False |

### 3.4 send_meeting_locked_notification()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Participant with email | participant.email, meeting_request, locked_slot | True, notification sent |
| Edge Case | Participant without email | participant.email=None | False immediately |
| Error Handling | Template rendering error | Mock render_to_string to raise exception | False, error handled |
| Integration | send_email_via_resend fails | Mock send_email_via_resend to return False | False |

### 3.5 send_password_reset_email()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Valid user | user with email, valid reset_url | True, reset email sent |
| Edge Case | Invalid reset_url | reset_url=malformed | Email sent with malformed URL or error |
| Error Handling | Template rendering error | Mock render_to_string to raise exception | False, error handled |
| Integration | send_email_via_resend fails | Mock send_email_via_resend to return False | False |

---

## 4. USER PROFILE METHODS (src/meetings/user_profile.py)

### 4.1 UserProfile.generate_verification_token()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | First generation | UserProfile with no token | 32-byte token generated, token_created_at set, saved |
| Basic Functionality | Regeneration | UserProfile with existing token | Old token replaced with new one, timestamp updated |
| Edge Case | Token uniqueness | Multiple calls | Each call generates different token |

### 4.2 UserProfile.is_verification_token_valid()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Just created | token_created_at=now | True |
| Boundary | At expiry boundary (23h 59m) | token_created_at=23h 59m ago, expiry=24h | True |
| Boundary | Just expired (24h 1m) | token_created_at=24h 1m ago, expiry=24h | False |
| Edge Case | Well expired | token_created_at=2 days ago | False |
| Edge Case | No token_created_at | token_created_at=None | False |
| Configuration | Custom expiry hours | EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=12, token_created_at=13h ago | False |

### 4.3 UserProfile.verify_email()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Unverified to verified | email_verified=False | email_verified=True, token cleared, saved |
| Edge Case | Already verified | email_verified=True | Remains True, token cleared |
| Validation | Token cleared | Before: token='abc123' | After: token=None or '' |

### 4.4 UserProfile.generate_password_reset_token()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | First generation | UserProfile with no reset token | 32-byte token generated, timestamp set, saved |
| Basic Functionality | Regeneration | UserProfile with existing reset token (multiple requests) | Old token replaced, timestamp updated |
| Edge Case | Token uniqueness | Multiple calls | Each generates different token |

### 4.5 UserProfile.is_password_reset_token_valid()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Just created | token_created_at=now | True |
| Boundary | At expiry boundary (59m) | token_created_at=59m ago, expiry=1h | True |
| Boundary | Just expired (1h 1m) | token_created_at=61m ago, expiry=1h | False |
| Edge Case | Well expired | token_created_at=24h ago | False |
| Edge Case | No token_created_at | token_created_at=None | False |
| Configuration | Custom expiry | PASSWORD_RESET_TOKEN_EXPIRY_HOURS=2, token_created_at=3h ago | False |

### 4.6 UserProfile.clear_password_reset_token()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Token exists | password_reset_token='abc123' | Token set to None, saved |
| Edge Case | No token | password_reset_token=None | Remains None, no error |
| Edge Case | Already cleared | Called twice | No error on second call |

---

## 5. FORM VALIDATION (src/meetings/forms.py)

### 5.1 UserRegistrationForm.clean_email()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Unique email | email='newuser@example.com', not in database | Email string returned |
| Basic Functionality | Duplicate email | email='existing@example.com', already in database | Raises ValidationError |
| Edge Case | Email case sensitivity | Database has 'User@Example.com', form has 'user@example.com' | Depends on DB collation (should handle) |

### 5.2 MeetingRequestForm.clean()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | All valid fields | All date ranges, work hours, deadline valid | cleaned_data returned |
| Date Range | Valid date range | date_range_start='2024-01-01', date_range_end='2024-01-10' | Valid |
| Date Range | Invalid date range (end <= start) | date_range_start='2024-01-10', date_range_end='2024-01-05' | Raises ValidationError |
| Date Range | Start date in past | date_range_start=yesterday | Raises ValidationError |
| Date Range | End date in past | date_range_end=yesterday | Raises ValidationError |
| Date Range | Date range > 90 days | date_range_start='2024-01-01', date_range_end='2024-05-01' (>90 days) | Raises ValidationError |
| Work Hours | Valid work hours | work_hours_start='09:00', work_hours_end='17:00' | Valid |
| Work Hours | Invalid work hours (end <= start) | work_hours_start='17:00', work_hours_end='09:00' | Raises ValidationError |
| Work Hours | Work hours equal | work_hours_start='09:00', work_hours_end='09:00' | Raises ValidationError |
| Deadline | Response deadline in past | response_deadline=yesterday | Raises ValidationError |
| Deadline | Response deadline in future | response_deadline=tomorrow | Valid |
| Deadline | No response deadline | response_deadline=None | Valid |

### 5.3 BusySlotForm.clean()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | Valid time range | start_time < end_time | cleaned_data returned |
| Edge Case | Invalid time range (end <= start) | start_time='10:00', end_time='09:00' | Raises ValidationError |
| Edge Case | Times equal | start_time='10:00', end_time='10:00' | Raises ValidationError |

---

## 6. VIEW HELPER FUNCTIONS (src/meetings/views.py)

### 6.1 get_or_create_creator_id()

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| Basic Functionality | First request (no session creator_id) | request.session without 'creator_id' | UUID generated, stored in session, returned |
| Basic Functionality | Subsequent request (has session creator_id) | request.session with 'creator_id'='existing-uuid' | Returns existing UUID, no new generation |
| Edge Case | Session expiry | Simulate expired session | New UUID generated |

---

## Summary

**Total Test Cases: 197**

### By Module:
- **utils.py**: 77 test cases
- **models.py**: 35 test cases
- **email_utils.py**: 29 test cases
- **user_profile.py**: 18 test cases
- **forms.py**: 15 test cases
- **views.py**: 3 test cases

### By Category:
- **Basic Functionality**: 71 test cases
- **Edge Cases**: 68 test cases
- **Error Handling**: 22 test cases
- **Timezone/Format**: 18 test cases
- **Boundary Tests**: 11 test cases
- **Integration Tests**: 7 test cases

### Test Coverage Priority:
1. **Critical Path (High Priority)**: Core scheduling algorithms - generate_time_slots, is_participant_available, calculate_slot_availability
2. **High Risk (High Priority)**: Email sending, token generation and validation
3. **Data Integrity (Medium Priority)**: Model validation, properties, form validation
4. **Supporting Functions (Medium Priority)**: Helper functions, utility methods
5. **View Helpers (Low Priority)**: Simple session management functions

### Mocking Requirements:
- Django ORM queries (Participant, BusySlot, SuggestedSlot, User)
- External APIs (Resend email service)
- Time-dependent functions (timezone.now())
- Token generation (secrets.token_urlsafe())
- Session management (request.session)
- Template rendering (render_to_string)

---

## Notes
- All test cases should use appropriate fixtures for Django models
- Mock external dependencies (Resend API, etc.)
- Use freezegun or similar for time-dependent tests
- Test both positive and negative paths
- Include boundary value analysis for numeric inputs
- Test timezone handling with multiple timezones including DST
- Performance tests for functions handling large datasets
- Integration tests should use test database
