"""
Unit tests for parse_busy_slots_from_json function
Tests parsing busy slots from JSON format
"""
import pytest
import pytz
from datetime import datetime
from meetings.utils import parse_busy_slots_from_json


class TestParseBusySlotsFromJson:
    """Test cases for parse_busy_slots_from_json function"""
    
    def test_empty_list(self):
        """Test parsing empty JSON list"""
        result = parse_busy_slots_from_json([], 'Asia/Ho_Chi_Minh')
        
        assert result == []
    
    def test_valid_json_with_iso_strings(self):
        """Test parsing valid JSON with ISO format strings"""
        json_data = [
            {
                'start': '2024-01-01T09:00:00',
                'end': '2024-01-01T10:00:00'
            }
        ]
        
        result = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        
        assert len(result) == 1
        start_utc, end_utc = result[0]
        
        # Verify times are in UTC
        assert start_utc.tzinfo == pytz.UTC
        assert end_utc.tzinfo == pytz.UTC
        
        # 09:00 Asia/Ho_Chi_Minh should be 02:00 UTC
        assert start_utc.hour == 2
        assert end_utc.hour == 3
    
    def test_json_with_z_suffix_utc(self):
        """Test parsing JSON with 'Z' suffix indicating UTC"""
        json_data = [
            {
                'start': '2024-01-01T09:00:00Z',
                'end': '2024-01-01T10:00:00Z'
            }
        ]
        
        result = parse_busy_slots_from_json(json_data, 'UTC')
        
        assert len(result) == 1
        start_utc, end_utc = result[0]
        
        assert start_utc.hour == 9
        assert end_utc.hour == 10
    
    def test_missing_start_key(self):
        """Test parsing JSON with missing 'start' key"""
        json_data = [
            {
                'end': '2024-01-01T10:00:00'
            }
        ]
        
        # Should skip invalid entries
        result = parse_busy_slots_from_json(json_data, 'UTC')
        assert len(result) == 0
    
    def test_missing_end_key(self):
        """Test parsing JSON with missing 'end' key"""
        json_data = [
            {
                'start': '2024-01-01T09:00:00'
            }
        ]
        
        # Should skip invalid entries
        result = parse_busy_slots_from_json(json_data, 'UTC')
        assert len(result) == 0
    
    def test_invalid_date_format(self):
        """Test parsing JSON with invalid date format"""
        json_data = [
            {
                'start': 'invalid-date',
                'end': '2024-01-01T10:00:00'
            }
        ]
        
        with pytest.raises(ValueError):
            parse_busy_slots_from_json(json_data, 'UTC')
    
    def test_invalid_timezone(self):
        """Test parsing with invalid timezone"""
        json_data = [
            {
                'start': '2024-01-01T09:00:00',
                'end': '2024-01-01T10:00:00'
            }
        ]
        
        with pytest.raises(pytz.exceptions.UnknownTimeZoneError):
            parse_busy_slots_from_json(json_data, 'Invalid/Timezone')
    
    def test_multiple_slots(self):
        """Test parsing multiple busy slots"""
        json_data = [
            {
                'start': '2024-01-01T09:00:00',
                'end': '2024-01-01T10:00:00'
            },
            {
                'start': '2024-01-01T14:00:00',
                'end': '2024-01-01T15:00:00'
            },
            {
                'start': '2024-01-02T09:00:00',
                'end': '2024-01-02T10:00:00'
            }
        ]
        
        result = parse_busy_slots_from_json(json_data, 'UTC')
        
        assert len(result) == 3
        
        # Verify all slots are properly parsed
        for start_utc, end_utc in result:
            assert start_utc.tzinfo == pytz.UTC
            assert end_utc.tzinfo == pytz.UTC
            assert start_utc < end_utc
    
    def test_timezone_conversion_accuracy(self):
        """Test accurate timezone conversion for different zones"""
        json_data = [
            {
                'start': '2024-01-01T12:00:00',
                'end': '2024-01-01T13:00:00'
            }
        ]
        
        # Test Asia/Ho_Chi_Minh (UTC+7)
        result_asia = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        assert result_asia[0][0].hour == 5  # 12:00 +7 = 05:00 UTC
        
        # Test America/New_York (UTC-5 in winter)
        result_ny = parse_busy_slots_from_json(json_data, 'America/New_York')
        assert result_ny[0][0].hour == 17  # 12:00 -5 = 17:00 UTC
