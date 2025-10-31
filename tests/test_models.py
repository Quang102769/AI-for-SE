"""
Unit tests for models.py
Tests for MeetingRequest, Participant, BusySlot, and SuggestedSlot models
"""
import pytest
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import pytz

from meetings.models import MeetingRequest, Participant, BusySlot, SuggestedSlot


# =============================================================================
# MeetingRequest Model Tests
# =============================================================================

class TestMeetingRequestSave:
    """Tests for MeetingRequest.save() method"""
    
    def test_first_save_generates_token(self, db):
        """Test that token is generated on first save"""
        meeting = MeetingRequest(
            title="Test Meeting",
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        assert not meeting.token
        meeting.save()
        assert meeting.token
        assert len(meeting.token) > 0
    
    def test_subsequent_save_keeps_token(self, db):
        """Test that existing token is unchanged on subsequent saves"""
        meeting = MeetingRequest.objects.create(
            title="Test Meeting",
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        original_token = meeting.token
        meeting.title = "Updated Title"
        meeting.save()
        assert meeting.token == original_token


class TestMeetingRequestIsActive:
    """Tests for MeetingRequest.is_active property"""
    
    def test_active_with_no_deadline(self, db, create_meeting_request):
        """Test that active meeting with no deadline is active"""
        meeting = create_meeting_request(status='active', response_deadline=None)
        assert meeting.is_active is True
    
    def test_active_with_future_deadline(self, db, create_meeting_request):
        """Test that active meeting with future deadline is active"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(status='active', response_deadline=future)
        assert meeting.is_active is True
    
    def test_active_with_past_deadline(self, db, create_meeting_request):
        """Test that active meeting with past deadline is not active"""
        past = timezone.now() - timedelta(days=1)
        meeting = create_meeting_request(status='active', response_deadline=past)
        assert meeting.is_active is False
    
    def test_status_locked(self, db, create_meeting_request):
        """Test that locked meeting is not active"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(status='locked', response_deadline=future)
        assert meeting.is_active is False
    
    def test_status_cancelled(self, db, create_meeting_request):
        """Test that cancelled meeting is not active"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(status='cancelled', response_deadline=future)
        assert meeting.is_active is False
    
    def test_status_draft(self, db, create_meeting_request):
        """Test that draft meeting is not active"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(status='draft', response_deadline=future)
        assert meeting.is_active is False


class TestMeetingRequestResponseRate:
    """Tests for MeetingRequest.response_rate property"""
    
    def test_no_participants(self, db, create_meeting_request):
        """Test response rate with no participants"""
        meeting = create_meeting_request()
        assert meeting.response_rate == 0
    
    def test_all_responded(self, db, create_meeting_request, create_participant):
        """Test response rate when all participants responded"""
        meeting = create_meeting_request()
        for i in range(5):
            create_participant(meeting, email=f"user{i}@test.com", has_responded=True)
        assert meeting.response_rate == 100
    
    def test_none_responded(self, db, create_meeting_request, create_participant):
        """Test response rate when no participants responded"""
        meeting = create_meeting_request()
        for i in range(5):
            create_participant(meeting, email=f"user{i}@test.com", has_responded=False)
        assert meeting.response_rate == 0
    
    def test_some_responded(self, db, create_meeting_request, create_participant):
        """Test response rate when some participants responded"""
        meeting = create_meeting_request()
        for i in range(5):
            responded = i < 3
            create_participant(meeting, email=f"user{i}@test.com", has_responded=responded)
        assert meeting.response_rate == 60
    
    def test_rounding(self, db, create_meeting_request, create_participant):
        """Test response rate rounding (1/3 = 33.33% -> 33)"""
        meeting = create_meeting_request()
        for i in range(3):
            responded = i < 1
            create_participant(meeting, email=f"user{i}@test.com", has_responded=responded)
        assert meeting.response_rate == 33


class TestMeetingRequestGetShareUrl:
    """Tests for MeetingRequest.get_share_url() method"""
    
    def test_valid_uuid_and_token(self, db, create_meeting_request):
        """Test share URL generation with valid UUID and token"""
        meeting = create_meeting_request()
        url = meeting.get_share_url()
        assert url == f"/r/{meeting.id}?t={meeting.token}"
    
    def test_special_characters_in_token(self, db, create_meeting_request):
        """Test share URL with special characters in token"""
        meeting = create_meeting_request()
        # Token generated by secrets.token_urlsafe should be URL-safe
        url = meeting.get_share_url()
        assert f"/r/{meeting.id}?t=" in url


# =============================================================================
# Participant Model Tests
# =============================================================================

class TestParticipantStr:
    """Tests for Participant.__str__() method"""
    
    def test_with_name_and_email(self, db, create_meeting_request, create_participant):
        """Test string representation with name and email"""
        meeting = create_meeting_request(title="Team Sync")
        participant = create_participant(
            meeting,
            name="John",
            email="john@example.com"
        )
        assert str(participant) == "John - Team Sync"
    
    def test_only_name(self, db, create_meeting_request, create_participant):
        """Test string representation with only name"""
        meeting = create_meeting_request(title="Team Sync")
        participant = create_participant(
            meeting,
            name="John",
            email=""
        )
        # String representation uses name when available
        assert "John" in str(participant)
        assert "Team Sync" in str(participant)
    
    def test_only_email(self, db, create_meeting_request, create_participant):
        """Test string representation with only email"""
        meeting = create_meeting_request(title="Team Sync")
        participant = create_participant(
            meeting,
            name="",
            email="john@example.com"
        )
        # When name is empty, email should be used
        result = str(participant)
        assert "Team Sync" in result


# =============================================================================
# BusySlot Model Tests
# =============================================================================

class TestBusySlotClean:
    """Tests for BusySlot.clean() validation method"""
    
    def test_valid_time_range(self, db, create_meeting_request, create_participant, create_utc_datetime):
        """Test that valid time range passes validation"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        
        busy_slot = BusySlot(
            participant=participant,
            start_time=start,
            end_time=end
        )
        # Should not raise ValidationError
        busy_slot.clean()
    
    def test_start_equals_end(self, db, create_meeting_request, create_participant, create_utc_datetime):
        """Test that start time equal to end time raises ValidationError"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        
        busy_slot = BusySlot(
            participant=participant,
            start_time=start,
            end_time=start
        )
        with pytest.raises(ValidationError):
            busy_slot.clean()
    
    def test_start_after_end(self, db, create_meeting_request, create_participant, create_utc_datetime):
        """Test that start time after end time raises ValidationError"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        start = create_utc_datetime(2024, 1, 1, 10, 0)
        end = create_utc_datetime(2024, 1, 1, 9, 0)
        
        busy_slot = BusySlot(
            participant=participant,
            start_time=start,
            end_time=end
        )
        with pytest.raises(ValidationError):
            busy_slot.clean()


# =============================================================================
# SuggestedSlot Model Tests
# =============================================================================

class TestSuggestedSlotAvailabilityPercentage:
    """Tests for SuggestedSlot.availability_percentage property"""
    
    def test_no_participants(self, db, create_meeting_request, create_suggested_slot, create_utc_datetime):
        """Test availability percentage with no participants"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        slot = create_suggested_slot(
            meeting,
            start,
            end,
            available_count=0,
            total_participants=0
        )
        assert slot.availability_percentage == 0.0
    
    def test_none_available(self, db, create_meeting_request, create_suggested_slot, create_utc_datetime):
        """Test availability percentage when none available"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        slot = create_suggested_slot(
            meeting,
            start,
            end,
            available_count=0,
            total_participants=5
        )
        assert slot.availability_percentage == 0.0
    
    def test_all_available(self, db, create_meeting_request, create_suggested_slot, create_utc_datetime):
        """Test availability percentage when all available"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        slot = create_suggested_slot(
            meeting,
            start,
            end,
            available_count=5,
            total_participants=5
        )
        assert slot.availability_percentage == 100.0
    
    def test_rounding_case_66_percent(self, db, create_meeting_request, create_suggested_slot, create_utc_datetime):
        """Test availability percentage rounding (2/3 = 66.666% -> 66.7)"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        slot = create_suggested_slot(
            meeting,
            start,
            end,
            available_count=2,
            total_participants=3
        )
        assert slot.availability_percentage == 66.7
    
    def test_rounding_case_33_percent(self, db, create_meeting_request, create_suggested_slot, create_utc_datetime):
        """Test availability percentage rounding (1/3 = 33.333% -> 33.3)"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        slot = create_suggested_slot(
            meeting,
            start,
            end,
            available_count=1,
            total_participants=3
        )
        assert slot.availability_percentage == 33.3


class TestSuggestedSlotHeatmapLevel:
    """Tests for SuggestedSlot.heatmap_level property"""
    
    @pytest.mark.parametrize("available,total,expected_level,scenario", [
        (0, 10, 0, "0%"),
        (1, 1000, 1, "0.1%"),
        (199, 1000, 1, "19.9%"),
        (2, 10, 2, "20% boundary"),
        (399, 1000, 2, "39.9%"),
        (4, 10, 3, "40% boundary"),
        (599, 1000, 3, "59.9%"),
        (6, 10, 4, "60% boundary"),
        (799, 1000, 4, "79.9%"),
        (8, 10, 5, "80% boundary"),
        (10, 10, 5, "100%"),
    ])
    def test_heatmap_levels(self, db, create_meeting_request, create_suggested_slot, 
                           create_utc_datetime, available, total, expected_level, scenario):
        """Test heatmap level for various availability percentages"""
        meeting = create_meeting_request()
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        
        slot = create_suggested_slot(
            meeting, start, end,
            available_count=available, 
            total_participants=total
        )
        
        assert slot.heatmap_level == expected_level, f"Failed: {scenario}"
