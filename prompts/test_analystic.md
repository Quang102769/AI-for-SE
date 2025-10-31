# Unit Testing Analysis - TimeWeave Meeting Scheduler

## Project Overview
TimeWeave is a Django-based meeting scheduling application that helps leaders find optimal meeting times by collecting participants' availability and calculating overlapping free time slots.

---

## 1. UTILITY FUNCTIONS (src/meetings/utils.py)

### 1.1 `generate_time_slots(meeting_request)`

**Main Functionality:**
- Generates all possible time slots based on meeting request configuration
- Iterates through date range and creates slots according to work hours and step size
- Handles timezone conversion from meeting timezone to UTC

**Input Parameters:**
- `meeting_request` (MeetingRequest): Django model instance containing configuration:
  - `date_range_start` (date): Start of scheduling range
  - `date_range_end` (date): End of scheduling range
  - `duration_minutes` (int): Meeting duration
  - `work_hours_start` (time): Daily work start time
  - `work_hours_end` (time): Daily work end time
  - `step_size_minutes` (int): Interval between slots (15, 30, or 60)
  - `work_days_only` (bool): Whether to skip weekends
  - `timezone` (str): Timezone string (e.g., 'Asia/Ho_Chi_Minh')

**Expected Return Values:**
- List of tuples: `[(start_datetime_utc, end_datetime_utc), ...]`
- All datetimes are timezone-aware in UTC

**Potential Edge Cases:**
- Single day date range
- Date range spanning weekends with `work_days_only=True`
- Date range spanning weekends with `work_days_only=False`
- Work hours that don't fit even one slot (duration > work hours)
- Duration exactly equals work hours minus step size
- Invalid timezone strings
- Date range crossing DST (Daylight Saving Time) boundaries
- Very long date ranges (performance testing)
- Step size larger than duration
- Slot that would end exactly at work_hours_end

**Dependencies to Mock:**
- None (uses standard library datetime and pytz)

---

### 1.2 `is_participant_available(participant, start_time, end_time)`

**Main Functionality:**
- Checks if a participant has any busy slots that overlap with the given time range
- Uses database query with Q objects for overlap detection

**Input Parameters:**
- `participant` (Participant): Django model instance
- `start_time` (datetime): Start of time slot to check (UTC)
- `end_time` (datetime): End of time slot to check (UTC)

**Expected Return Values:**
- `True` if participant is available (no conflicts)
- `False` if participant has conflicting busy slots

**Potential Edge Cases:**
- Participant with no busy slots (should return True)
- Busy slot starts exactly when check slot ends (should return True - no overlap)
- Busy slot ends exactly when check slot starts (should return True - no overlap)
- Busy slot completely contains check slot
- Check slot completely contains busy slot
- Busy slot partially overlaps at start
- Busy slot partially overlaps at end
- Multiple overlapping busy slots
- Participant with has_responded=False

**Dependencies to Mock:**
- `BusySlot.objects.filter()` - Django ORM query

---

### 1.3 `calculate_slot_availability(meeting_request, start_time, end_time)`

**Main Functionality:**
- Calculates how many participants who have responded are available for a specific time slot
- Aggregates availability across all participants

**Input Parameters:**
- `meeting_request` (MeetingRequest): Django model instance
- `start_time` (datetime): Start of time slot (UTC)
- `end_time` (datetime): End of time slot (UTC)

**Expected Return Values:**
- Tuple: `(available_count, total_count, participant_ids_available)`
  - `available_count` (int): Number of available participants
  - `total_count` (int): Total participants who responded
  - `participant_ids_available` (list): List of available participant IDs

**Potential Edge Cases:**
- Meeting request with no participants
- Meeting request with participants but none have responded
- All participants available
- No participants available
- Some participants available, some not
- Participants with overlapping busy slots at different times

**Dependencies to Mock:**
- `Participant.objects.filter()` - Django ORM query
- `is_participant_available()` - Internal function call

---

### 1.4 `generate_suggested_slots(meeting_request, force_recalculate=False)`

**Main Functionality:**
- Main algorithm that generates suggested time slots with availability data
- Creates SuggestedSlot objects in database
- Can force recalculation by deleting existing suggestions

**Input Parameters:**
- `meeting_request` (MeetingRequest): Django model instance
- `force_recalculate` (bool): Whether to delete and regenerate all slots (default: False)

**Expected Return Values:**
- List of `SuggestedSlot` objects

**Potential Edge Cases:**
- First time generation (no existing slots)
- Regeneration with force_recalculate=True
- Regeneration with force_recalculate=False
- Meeting request configuration change requiring regeneration
- No possible slots (all times busy for all participants)
- All slots have 100% availability
- Database update vs create logic (update_or_create)
- Large number of slots (performance)

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter().delete()` - Django ORM
- `SuggestedSlot.objects.update_or_create()` - Django ORM
- `generate_time_slots()` - Internal function
- `calculate_slot_availability()` - Internal function

---

### 1.5 `get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)`

**Main Functionality:**
- Retrieves and filters top suggested slots based on availability
- Sorts by availability count and start time
- Filters by minimum availability percentage

**Input Parameters:**
- `meeting_request` (MeetingRequest): Django model instance
- `limit` (int): Maximum number of suggestions to return (default: 10)
- `min_availability_pct` (int): Minimum availability percentage threshold (default: 50)

**Expected Return Values:**
- List of `SuggestedSlot` objects (max length = limit)
- Sorted by available_count descending, then start_time ascending

**Potential Edge Cases:**
- No slots meet minimum availability threshold
- Fewer slots than limit available
- Exactly limit slots available
- More slots than limit available
- All slots have same availability count
- min_availability_pct = 0
- min_availability_pct = 100
- Limit = 0
- Negative limit

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter().order_by()` - Django ORM query

---

### 1.6 `get_heatmap_data(meeting_request, participant_timezone='Asia/Ho_Chi_Minh')`

**Main Functionality:**
- Generates heatmap visualization data structure
- Converts UTC times to participant's timezone
- Organizes data by date and time for frontend display
- Handles both cases: with and without existing SuggestedSlot data

**Input Parameters:**
- `meeting_request` (MeetingRequest): Django model instance
- `participant_timezone` (str): Timezone for display (default: 'Asia/Ho_Chi_Minh')

**Expected Return Values:**
- Dictionary with structure:
```python
{
    'dates': ['2024-01-01', '2024-01-02', ...],
    'time_slots': ['09:00', '09:30', '10:00', ...],
    'heatmap': {
        '2024-01-01': {
            '09:00': {
                'level': 5, 
                'available': 10, 
                'total': 10,
                'percentage': 100.0,
                'start_utc': '2024-01-01T02:00:00+00:00',
                'end_utc': '2024-01-01T03:00:00+00:00'
            },
            ...
        },
        ...
    },
    'timezone': 'Asia/Ho_Chi_Minh'
}
```

**Potential Edge Cases:**
- No suggested slots exist (generates from meeting config)
- Suggested slots exist
- Different participant timezones (UTC, EST, JST, etc.)
- Single date with multiple times
- Multiple dates with single time
- Empty date range
- Invalid timezone string
- Timezone conversion across DST boundaries

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter()` - Django ORM
- `generate_time_slots()` - Internal function (when no slots exist)

---

### 1.7 `format_datetime_for_timezone(dt, timezone_str)`

**Main Functionality:**
- Converts and formats a datetime to a specific timezone
- Handles both naive and timezone-aware datetimes

**Input Parameters:**
- `dt` (datetime): DateTime object to format
- `timezone_str` (str): Target timezone string

**Expected Return Values:**
- String in format: 'YYYY-MM-DD HH:MM'

**Potential Edge Cases:**
- Naive datetime (assumes UTC)
- Timezone-aware datetime
- UTC timezone
- Different timezones (EST, JST, etc.)
- DST boundary times
- Invalid timezone string

**Dependencies to Mock:**
- None (uses standard library)

---

### 1.8 `parse_busy_slots_from_json(json_data, participant_timezone)`

**Main Functionality:**
- Parses busy slot data from frontend JSON format
- Converts participant timezone to UTC
- Handles both naive and timezone-aware datetime strings

**Input Parameters:**
- `json_data` (list): List of dictionaries with 'start' and 'end' keys
  - Example: `[{'start': '2024-01-01T09:00', 'end': '2024-01-01T10:00'}, ...]`
- `participant_timezone` (str): Participant's timezone string

**Expected Return Values:**
- List of tuples: `[(start_datetime_utc, end_datetime_utc), ...]`

**Potential Edge Cases:**
- Empty list
- Single slot
- Multiple slots
- Naive datetime strings (no timezone)
- ISO format with 'Z' suffix (UTC indicator)
- ISO format with timezone offset
- Missing 'start' or 'end' keys
- Invalid datetime format
- Empty strings for start/end
- Invalid timezone string

**Dependencies to Mock:**
- None (uses standard library)

---

## 2. MODEL METHODS (src/meetings/models.py)

### 2.1 `MeetingRequest.save()`

**Main Functionality:**
- Overrides default save to auto-generate unique token

**Input Parameters:**
- Standard Django model save parameters

**Expected Return Values:**
- None (saves to database)

**Potential Edge Cases:**
- First save (token should be generated)
- Subsequent saves (token should not change)
- Token collision (very unlikely but should handle)

**Dependencies to Mock:**
- `secrets.token_urlsafe()` - Token generation
- Django ORM save

---

### 2.2 `MeetingRequest.is_active` (property)

**Main Functionality:**
- Determines if a meeting request is still accepting responses
- Checks status and deadline

**Input Parameters:**
- None (property)

**Expected Return Values:**
- `True` if active
- `False` if not active

**Potential Edge Cases:**
- Status = 'active', no deadline
- Status = 'active', deadline in future
- Status = 'active', deadline in past
- Status = 'locked'
- Status = 'cancelled'
- Status = 'draft'

**Dependencies to Mock:**
- `timezone.now()` - Current time

---

### 2.3 `MeetingRequest.response_rate` (property)

**Main Functionality:**
- Calculates percentage of participants who have responded

**Input Parameters:**
- None (property)

**Expected Return Values:**
- Integer 0-100 representing percentage

**Potential Edge Cases:**
- No participants (should return 0)
- All participants responded
- No participants responded
- Some participants responded
- Rounding edge cases

**Dependencies to Mock:**
- `self.participants.count()` - Django ORM
- `self.participants.filter().count()` - Django ORM

---

### 2.4 `MeetingRequest.get_share_url()`

**Main Functionality:**
- Generates the shareable URL path for participants

**Input Parameters:**
- None

**Expected Return Values:**
- String in format: `/r/{id}?t={token}`

**Potential Edge Cases:**
- Valid UUID and token
- Special characters in token (URL encoding)

**Dependencies to Mock:**
- None

---

### 2.5 `Participant.__str__()`

**Main Functionality:**
- String representation of participant

**Input Parameters:**
- None

**Expected Return Values:**
- String with participant name/email and meeting title

**Potential Edge Cases:**
- Participant with name and email
- Participant with only name
- Participant with only email
- Participant with neither (anonymous)

**Dependencies to Mock:**
- None

---

### 2.6 `BusySlot.clean()`

**Main Functionality:**
- Validates that end_time is after start_time

**Input Parameters:**
- None (validates model fields)

**Expected Return Values:**
- None if valid
- Raises `ValidationError` if invalid

**Potential Edge Cases:**
- start_time < end_time (valid)
- start_time = end_time (invalid)
- start_time > end_time (invalid)

**Dependencies to Mock:**
- None

---

### 2.7 `SuggestedSlot.availability_percentage` (property)

**Main Functionality:**
- Calculates availability percentage rounded to 1 decimal place

**Input Parameters:**
- None (property)

**Expected Return Values:**
- Float 0.0-100.0 with 1 decimal place

**Potential Edge Cases:**
- total_participants = 0 (should return 0)
- available_count = 0
- available_count = total_participants (100%)
- Rounding cases (e.g., 66.666... → 66.7)

**Dependencies to Mock:**
- None

---

### 2.8 `SuggestedSlot.heatmap_level` (property)

**Main Functionality:**
- Returns heatmap intensity level 0-5 based on availability percentage

**Input Parameters:**
- None (property)

**Expected Return Values:**
- Integer 0-5:
  - 5: 80%+
  - 4: 60-79%
  - 3: 40-59%
  - 2: 20-39%
  - 1: 1-19%
  - 0: 0%

**Potential Edge Cases:**
- 0% availability → 0
- 0.1% availability → 1
- 19.9% availability → 1
- 20% exactly → 2
- 79.9% availability → 4
- 80% exactly → 5
- 100% availability → 5

**Dependencies to Mock:**
- `self.availability_percentage` property

---

## 3. EMAIL UTILITY FUNCTIONS (src/meetings/email_utils.py)

### 3.1 `send_email_via_resend(to_email, subject, html_content, from_email=None)`

**Main Functionality:**
- Sends email using Resend API
- Falls back to console logging in development

**Input Parameters:**
- `to_email` (str or list): Recipient email(s)
- `subject` (str): Email subject
- `html_content` (str): HTML email body
- `from_email` (str, optional): Sender email

**Expected Return Values:**
- `True` if sent successfully
- `False` if failed or API key not configured

**Potential Edge Cases:**
- API key not configured
- Single email recipient
- Multiple email recipients
- Invalid email format
- Resend API error
- Network timeout
- Empty subject/content

**Dependencies to Mock:**
- `resend.Emails.send()` - Resend API call
- `settings.RESEND_API_KEY` - Configuration
- `settings.DEFAULT_FROM_EMAIL` - Configuration

---

### 3.2 `send_verification_email(user, verification_url)`

**Main Functionality:**
- Sends email verification link to new users

**Input Parameters:**
- `user` (User): Django User instance
- `verification_url` (str): Full URL for verification

**Expected Return Values:**
- `True` if sent successfully
- `False` if failed

**Potential Edge Cases:**
- Valid user with email
- User without email
- Invalid verification URL
- Template rendering error

**Dependencies to Mock:**
- `render_to_string()` - Template rendering
- `send_email_via_resend()` - Email sending

---

### 3.3 `send_meeting_invitation_email(participant, meeting_request, respond_url)`

**Main Functionality:**
- Sends meeting invitation to participant

**Input Parameters:**
- `participant` (Participant): Participant instance
- `meeting_request` (MeetingRequest): Meeting instance
- `respond_url` (str): Full URL to respond

**Expected Return Values:**
- `True` if sent successfully
- `False` if failed or participant has no email

**Potential Edge Cases:**
- Participant with email
- Participant without email (should return False immediately)
- Invalid respond URL
- Template rendering error

**Dependencies to Mock:**
- `render_to_string()` - Template rendering
- `send_email_via_resend()` - Email sending

---

### 3.4 `send_meeting_locked_notification(participant, meeting_request, locked_slot)`

**Main Functionality:**
- Notifies participant that meeting time has been finalized

**Input Parameters:**
- `participant` (Participant): Participant instance
- `meeting_request` (MeetingRequest): Meeting instance
- `locked_slot` (SuggestedSlot): Finalized time slot

**Expected Return Values:**
- `True` if sent successfully
- `False` if failed or participant has no email

**Potential Edge Cases:**
- Participant with email
- Participant without email
- Template rendering error

**Dependencies to Mock:**
- `render_to_string()` - Template rendering
- `send_email_via_resend()` - Email sending

---

### 3.5 `send_password_reset_email(user, reset_url)`

**Main Functionality:**
- Sends password reset link to user

**Input Parameters:**
- `user` (User): Django User instance
- `reset_url` (str): Full URL for password reset

**Expected Return Values:**
- `True` if sent successfully
- `False` if failed

**Potential Edge Cases:**
- Valid user with email
- Invalid reset URL
- Template rendering error

**Dependencies to Mock:**
- `render_to_string()` - Template rendering
- `send_email_via_resend()` - Email sending

---

## 4. USER PROFILE METHODS (src/meetings/user_profile.py)

### 4.1 `UserProfile.generate_verification_token()`

**Main Functionality:**
- Generates unique email verification token
- Sets creation timestamp

**Input Parameters:**
- None

**Expected Return Values:**
- String: 32-byte URL-safe token

**Potential Edge Cases:**
- First time generation
- Regeneration (should replace old token)
- Token uniqueness

**Dependencies to Mock:**
- `secrets.token_urlsafe()` - Token generation
- `timezone.now()` - Timestamp
- Django ORM save

---

### 4.2 `UserProfile.is_verification_token_valid()`

**Main Functionality:**
- Checks if verification token has not expired

**Input Parameters:**
- None

**Expected Return Values:**
- `True` if valid and not expired
- `False` if expired or no token

**Potential Edge Cases:**
- Token just created (should be valid)
- Token at expiry boundary (23h 59m vs 24h 1m)
- Token well expired
- No token_created_at (should return False)
- Custom expiry hours setting

**Dependencies to Mock:**
- `timezone.now()` - Current time
- `settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS` - Configuration

---

### 4.3 `UserProfile.verify_email()`

**Main Functionality:**
- Marks email as verified and clears token

**Input Parameters:**
- None

**Expected Return Values:**
- None (updates model)

**Potential Edge Cases:**
- Unverified email → verified
- Already verified email
- Token should be cleared

**Dependencies to Mock:**
- Django ORM save

---

### 4.4 `UserProfile.generate_password_reset_token()`

**Main Functionality:**
- Generates unique password reset token
- Sets creation timestamp

**Input Parameters:**
- None

**Expected Return Values:**
- String: 32-byte URL-safe token

**Potential Edge Cases:**
- First time generation
- Regeneration (multiple reset requests)
- Token uniqueness

**Dependencies to Mock:**
- `secrets.token_urlsafe()` - Token generation
- `timezone.now()` - Timestamp
- Django ORM save

---

### 4.5 `UserProfile.is_password_reset_token_valid()`

**Main Functionality:**
- Checks if password reset token has not expired

**Input Parameters:**
- None

**Expected Return Values:**
- `True` if valid and not expired
- `False` if expired or no token

**Potential Edge Cases:**
- Token just created
- Token at expiry boundary
- Token expired
- No token_created_at
- Custom expiry hours setting (typically 1 hour)

**Dependencies to Mock:**
- `timezone.now()` - Current time
- `settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS` - Configuration

---

### 4.6 `UserProfile.clear_password_reset_token()`

**Main Functionality:**
- Clears password reset token after successful reset

**Input Parameters:**
- None

**Expected Return Values:**
- None (updates model)

**Potential Edge Cases:**
- Token exists
- No token exists
- Already cleared token

**Dependencies to Mock:**
- Django ORM save

---

## 5. FORM VALIDATION (src/meetings/forms.py)

### 5.1 `UserRegistrationForm.clean_email()`

**Main Functionality:**
- Validates email is unique in database

**Input Parameters:**
- None (validates form field)

**Expected Return Values:**
- Email string if valid
- Raises `ValidationError` if email exists

**Potential Edge Cases:**
- New unique email
- Duplicate email
- Email case sensitivity

**Dependencies to Mock:**
- `User.objects.filter()` - Django ORM

---

### 5.2 `MeetingRequestForm.clean()`

**Main Functionality:**
- Cross-field validation for meeting request
- Validates date ranges, work hours, deadlines

**Input Parameters:**
- None (validates form fields)

**Expected Return Values:**
- `cleaned_data` dictionary if valid
- Raises `ValidationError` if invalid

**Potential Edge Cases:**
- Valid date range (start < end)
- Invalid date range (end <= start)
- Start date in past
- End date in past
- Date range > 90 days
- Valid work hours (start < end)
- Invalid work hours (end <= start)
- Response deadline in past
- Response deadline in future
- All valid fields

**Dependencies to Mock:**
- `timezone.now()` - Current time

---

### 5.3 `BusySlotForm.clean()`

**Main Functionality:**
- Validates busy slot time range

**Input Parameters:**
- None (validates form fields)

**Expected Return Values:**
- `cleaned_data` dictionary if valid
- Raises `ValidationError` if invalid

**Potential Edge Cases:**
- Valid time range (start < end)
- Invalid time range (end <= start)
- start = end
- start > end

**Dependencies to Mock:**
- None

---

## 6. VIEW HELPER FUNCTIONS (src/meetings/views.py)

### 6.1 `get_or_create_creator_id(request)`

**Main Functionality:**
- Gets or creates a unique session-based creator ID

**Input Parameters:**
- `request` (HttpRequest): Django request object

**Expected Return Values:**
- String: UUID creator ID

**Potential Edge Cases:**
- First request (no session creator_id)
- Subsequent requests (has session creator_id)
- Session expiry

**Dependencies to Mock:**
- `uuid.uuid4()` - UUID generation
- `request.session` - Django session

---

## Summary Statistics

**Total Functions to Test: 41**

### By Module:
- **utils.py**: 8 functions
- **models.py**: 8 methods
- **email_utils.py**: 5 functions
- **user_profile.py**: 6 methods
- **forms.py**: 3 validation methods
- **views.py**: 1 helper function

### By Complexity:
- **High Complexity** (10+ edge cases): 6 functions
  - `generate_time_slots()`
  - `is_participant_available()`
  - `get_heatmap_data()`
  - `parse_busy_slots_from_json()`
  - `MeetingRequestForm.clean()`
  - `send_email_via_resend()`

- **Medium Complexity** (5-9 edge cases): 15 functions

- **Low Complexity** (<5 edge cases): 20 functions

### Priority for Testing:
1. **Critical Path**: Core scheduling algorithms (utils.py)
2. **High Risk**: Email sending and verification (email_utils.py, user_profile.py)
3. **Data Integrity**: Model validation and properties
4. **User Input**: Form validation

---

## Notes

- All database queries should be mocked or use test database fixtures
- Timezone handling requires careful testing with multiple timezones
- Email functions need mocking of external Resend API
- Form validation should test both valid and invalid inputs
- Model properties should test edge cases and calculations
- Performance testing recommended for functions handling large datasets
