"""
Extended unit tests for models.py
Tests model methods, properties, and validation
"""
import pytest
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from meetings.models import MeetingRequest, Participant, BusySlot, SuggestedSlot
import pytz


@pytest.mark.django_db
class TestMeetingRequestSave:
    """Test cases for MeetingRequest.save() method"""
    
    def test_first_save_no_token(self):
        """Test first save generates token"""
        meeting = MeetingRequest(
            title='Test Meeting',
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        assert not meeting.token
        meeting.save()
        
        assert meeting.token
        assert len(meeting.token) > 0
    
    def test_update_save_preserves_token(self):
        """Test update save preserves existing token"""
        meeting = MeetingRequest.objects.create(
            title='Test Meeting',
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        original_token = meeting.token
        
        meeting.title = 'Updated Meeting'
        meeting.save()
        
        assert meeting.token == original_token
    
    def test_token_uniqueness(self):
        """Test that multiple meetings get unique tokens"""
        meeting1 = MeetingRequest.objects.create(
            title='Meeting 1',
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        meeting2 = MeetingRequest.objects.create(
            title='Meeting 2',
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        assert meeting1.token != meeting2.token


@pytest.mark.django_db
class TestMeetingRequestIsActive:
    """Test cases for MeetingRequest.is_active property"""
    
    def test_active_with_no_deadline(self, create_meeting_request):
        """Test is_active when status is active and no deadline"""
        meeting = create_meeting_request(
            status='active',
            response_deadline=None
        )
        
        assert meeting.is_active is True
    
    def test_active_with_future_deadline(self, create_meeting_request):
        """Test is_active with future deadline"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(
            status='active',
            response_deadline=future
        )
        
        assert meeting.is_active is True
    
    def test_active_with_past_deadline(self, create_meeting_request):
        """Test is_active with past deadline"""
        past = timezone.now() - timedelta(days=1)
        meeting = create_meeting_request(
            status='active',
            response_deadline=past
        )
        
        assert meeting.is_active is False
    
    def test_locked_status(self, create_meeting_request):
        """Test is_active when status is locked"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(
            status='locked',
            response_deadline=future
        )
        
        assert meeting.is_active is False
    
    def test_cancelled_status(self, create_meeting_request):
        """Test is_active when status is cancelled"""
        future = timezone.now() + timedelta(days=1)
        meeting = create_meeting_request(
            status='cancelled',
            response_deadline=future
        )
        
        assert meeting.is_active is False


@pytest.mark.django_db
class TestMeetingRequestResponseRate:
    """Test cases for MeetingRequest.response_rate property"""
    
    def test_no_participants(self, create_meeting_request):
        """Test response_rate with no participants"""
        meeting = create_meeting_request()
        
        assert meeting.response_rate == 0
    
    def test_no_responses(self, create_meeting_request, create_participant):
        """Test response_rate with no responses"""
        meeting = create_meeting_request()
        
        for i in range(5):
            create_participant(meeting, has_responded=False)
        
        assert meeting.response_rate == 0
    
    def test_all_responded(self, create_meeting_request, create_participant):
        """Test response_rate when all responded"""
        meeting = create_meeting_request()
        
        for i in range(5):
            create_participant(meeting, has_responded=True)
        
        assert meeting.response_rate == 100
    
    def test_partial_responses(self, create_meeting_request, create_participant):
        """Test response_rate with partial responses"""
        meeting = create_meeting_request()
        
        for i in range(7):
            create_participant(meeting, has_responded=True)
        for i in range(3):
            create_participant(meeting, has_responded=False)
        
        assert meeting.response_rate == 70
    
    def test_single_participant_responded(self, create_meeting_request, create_participant):
        """Test response_rate with single responded participant"""
        meeting = create_meeting_request()
        create_participant(meeting, has_responded=True)
        
        assert meeting.response_rate == 100
    
    def test_single_participant_not_responded(self, create_meeting_request, create_participant):
        """Test response_rate with single non-responded participant"""
        meeting = create_meeting_request()
        create_participant(meeting, has_responded=False)
        
        assert meeting.response_rate == 0


@pytest.mark.django_db
class TestMeetingRequestGetShareUrl:
    """Test cases for MeetingRequest.get_share_url method"""
    
    def test_valid_id_and_token(self, create_meeting_request):
        """Test get_share_url with valid ID and token"""
        meeting = create_meeting_request()
        
        url = meeting.get_share_url()
        
        assert f'/r/{meeting.id}' in url
        assert f't={meeting.token}' in url
    
    def test_with_very_long_token(self):
        """Test get_share_url with very long token"""
        meeting = MeetingRequest.objects.create(
            title='Test',
            duration_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        # Token should be generated automatically
        url = meeting.get_share_url()
        
        assert 't=' in url
        assert len(url) > 0


@pytest.mark.django_db
class TestBusySlotClean:
    """Test cases for BusySlot.clean() validation"""
    
    def test_valid_time_range(self, create_meeting_request, create_participant, create_utc_datetime):
        """Test clean with valid time range (end after start)"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        
        busy_slot = BusySlot(
            participant=participant,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0)
        )
        
        # Should not raise exception
        busy_slot.clean()
    
    def test_invalid_end_before_start(self, create_meeting_request, create_participant, create_utc_datetime):
        """Test clean with end before start"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        
        busy_slot = BusySlot(
            participant=participant,
            start_time=create_utc_datetime(2024, 1, 1, 10, 0),
            end_time=create_utc_datetime(2024, 1, 1, 9, 0)
        )
        
        with pytest.raises(ValidationError):
            busy_slot.clean()
    
    def test_invalid_end_equals_start(self, create_meeting_request, create_participant, create_utc_datetime):
        """Test clean with end equals start"""
        meeting = create_meeting_request()
        participant = create_participant(meeting)
        
        same_time = create_utc_datetime(2024, 1, 1, 9, 0)
        busy_slot = BusySlot(
            participant=participant,
            start_time=same_time,
            end_time=same_time
        )
        
        with pytest.raises(ValidationError):
            busy_slot.clean()


@pytest.mark.django_db
class TestSuggestedSlotAvailabilityPercentage:
    """Test cases for SuggestedSlot.availability_percentage property"""
    
    def test_zero_total_participants(self, create_meeting_request, create_utc_datetime):
        """Test availability_percentage with 0 total participants (division by zero)"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=0,
            total_participants=0
        )
        
        assert slot.availability_percentage == 0.0
    
    def test_all_available_100_percent(self, create_meeting_request, create_utc_datetime):
        """Test availability_percentage with 100% availability"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=10,
            total_participants=10
        )
        
        assert slot.availability_percentage == 100.0
    
    def test_none_available_0_percent(self, create_meeting_request, create_utc_datetime):
        """Test availability_percentage with 0% availability"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=0,
            total_participants=10
        )
        
        assert slot.availability_percentage == 0.0
    
    def test_partial_availability(self, create_meeting_request, create_utc_datetime):
        """Test availability_percentage with partial availability"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=7,
            total_participants=10
        )
        
        assert slot.availability_percentage == 70.0
    
    def test_rounding(self, create_meeting_request, create_utc_datetime):
        """Test availability_percentage rounding"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=2,
            total_participants=3
        )
        
        # 2/3 = 66.666... should round to 66.7
        assert slot.availability_percentage == 66.7


@pytest.mark.django_db
class TestSuggestedSlotHeatmapLevel:
    """Test cases for SuggestedSlot.heatmap_level property"""
    
    @pytest.mark.parametrize('available,total,expected_level', [
        (0, 10, 0),   # 0%
        (1, 10, 1),   # 10%
        (2, 10, 2),   # 20%
        (3, 10, 2),   # 30%
        (4, 10, 3),   # 40%
        (5, 10, 3),   # 50%
        (6, 10, 4),   # 60%
        (7, 10, 4),   # 70%
        (8, 10, 5),   # 80%
        (9, 10, 5),   # 90%
        (10, 10, 5),  # 100%
    ])
    def test_heatmap_level_boundaries(
        self, create_meeting_request, create_utc_datetime, 
        available, total, expected_level
    ):
        """Test heatmap_level at various availability percentages"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=available,
            total_participants=total
        )
        
        assert slot.heatmap_level == expected_level
    
    def test_boundary_20_percent(self, create_meeting_request, create_utc_datetime):
        """Test heatmap_level at exactly 20%"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=2,
            total_participants=10
        )
        
        assert slot.heatmap_level == 2
    
    def test_boundary_40_percent(self, create_meeting_request, create_utc_datetime):
        """Test heatmap_level at exactly 40%"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=4,
            total_participants=10
        )
        
        assert slot.heatmap_level == 3
    
    def test_boundary_60_percent(self, create_meeting_request, create_utc_datetime):
        """Test heatmap_level at exactly 60%"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=6,
            total_participants=10
        )
        
        assert slot.heatmap_level == 4
    
    def test_boundary_80_percent(self, create_meeting_request, create_utc_datetime):
        """Test heatmap_level at exactly 80%"""
        meeting = create_meeting_request()
        slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=8,
            total_participants=10
        )
        
        assert slot.heatmap_level == 5
