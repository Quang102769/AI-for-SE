"""
Unit tests for get_heatmap_data function
Tests heatmap generation for visualization
"""
import pytest
import pytz
from datetime import datetime, date, time
from meetings.utils import get_heatmap_data
from meetings.models import SuggestedSlot


@pytest.mark.django_db
class TestGetHeatmapData:
    """Test cases for get_heatmap_data function"""
    
    def test_with_suggested_slots(self, create_meeting_request, create_utc_datetime):
        """Test heatmap generation with existing suggested slots"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2),
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        # Create suggested slots
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=8,
            total_participants=10
        )
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 10, 0),
            end_time=create_utc_datetime(2024, 1, 1, 11, 0),
            available_count=5,
            total_participants=10
        )
        
        # Generate heatmap
        heatmap_data = get_heatmap_data(meeting, participant_timezone='Asia/Ho_Chi_Minh')
        
        assert 'dates' in heatmap_data
        assert 'time_slots' in heatmap_data
        assert 'heatmap' in heatmap_data
        assert 'timezone' in heatmap_data
        assert heatmap_data['timezone'] == 'Asia/Ho_Chi_Minh'
        assert len(heatmap_data['dates']) > 0
        
        # Check that times are converted to Asia/Ho_Chi_Minh (+7 hours)
        first_date = heatmap_data['dates'][0]
        assert first_date in heatmap_data['heatmap']
        assert '16:00' in heatmap_data['heatmap'][first_date]  # 09:00 UTC = 16:00 +7
    
    def test_no_suggested_slots_generate_from_scratch(self, create_meeting_request):
        """Test heatmap generation when no suggested slots exist"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 15),
            date_range_end=date(2024, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='UTC')
        
        assert 'dates' in heatmap_data
        assert 'time_slots' in heatmap_data
        assert 'heatmap' in heatmap_data
        assert len(heatmap_data['dates']) > 0
        
        # All slots should have level 0 (no availability data)
        for date_str, time_data in heatmap_data['heatmap'].items():
            for time_str, slot_data in time_data.items():
                assert slot_data['level'] == 0
                assert slot_data['available'] == 0
                assert slot_data['total'] == 0
    
    def test_empty_date_range(self, create_meeting_request):
        """Test heatmap with invalid date range"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2023, 12, 31),  # End before start
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0),
            timezone='UTC'
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='UTC')
        
        # Should return empty or minimal data
        assert 'dates' in heatmap_data
        assert len(heatmap_data['dates']) == 0
    
    def test_single_date(self, create_meeting_request, create_utc_datetime):
        """Test heatmap with single date"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 15),
            date_range_end=date(2024, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='UTC')
        
        assert len(heatmap_data['dates']) == 1
        assert heatmap_data['dates'][0] == '2024-01-15'
    
    def test_cross_timezone_conversion_utc_to_asia_ho_chi_minh(
        self, create_meeting_request, create_utc_datetime
    ):
        """Test timezone conversion from UTC to Asia/Ho_Chi_Minh (+7 hours)"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        # Create a slot at 09:00 UTC
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=5,
            total_participants=10
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='Asia/Ho_Chi_Minh')
        
        # 09:00 UTC should be 16:00 in Asia/Ho_Chi_Minh
        assert '16:00' in heatmap_data['time_slots']
    
    def test_different_participant_timezone_america_new_york(
        self, create_meeting_request, create_utc_datetime
    ):
        """Test timezone conversion to America/New_York"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(14, 0),
            work_hours_end=time(16, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        # Create a slot at 14:00 UTC
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 14, 0),
            end_time=create_utc_datetime(2024, 1, 1, 15, 0),
            available_count=5,
            total_participants=10
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='America/New_York')
        
        # 14:00 UTC should be 09:00 EST (UTC-5 in winter)
        assert '09:00' in heatmap_data['time_slots']
    
    def test_slots_with_zero_percent_availability(
        self, create_meeting_request, create_utc_datetime
    ):
        """Test heatmap with 0% availability slots"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=0,
            total_participants=10
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='UTC')
        
        slot_data = heatmap_data['heatmap']['2024-01-01']['09:00']
        assert slot_data['level'] == 0
        assert slot_data['available'] == 0
        assert slot_data['percentage'] == 0.0
    
    def test_slots_with_hundred_percent_availability(
        self, create_meeting_request, create_utc_datetime
    ):
        """Test heatmap with 100% availability slots"""
        meeting = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            step_size_minutes=60,
            duration_minutes=60,
            timezone='UTC'
        )
        
        SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=10,
            total_participants=10
        )
        
        heatmap_data = get_heatmap_data(meeting, participant_timezone='UTC')
        
        slot_data = heatmap_data['heatmap']['2024-01-01']['09:00']
        assert slot_data['level'] == 5
        assert slot_data['available'] == 10
        assert slot_data['percentage'] == 100.0
