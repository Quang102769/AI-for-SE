"""
Unit tests for format_datetime_for_timezone function
Tests datetime formatting for different timezones
"""
import pytest
import pytz
from datetime import datetime
from meetings.utils import format_datetime_for_timezone


class TestFormatDatetimeForTimezone:
    """Test cases for format_datetime_for_timezone function"""
    
    def test_naive_datetime(self):
        """Test formatting naive datetime (no timezone info)"""
        naive_dt = datetime(2024, 1, 1, 9, 0)
        result = format_datetime_for_timezone(naive_dt, 'Asia/Ho_Chi_Minh')
        
        # Naive datetime is treated as UTC, then converted to Asia/Ho_Chi_Minh (+7)
        assert result == '2024-01-01 16:00'
    
    def test_aware_datetime_in_utc(self):
        """Test formatting aware datetime in UTC"""
        utc_dt = pytz.UTC.localize(datetime(2024, 1, 1, 2, 0))
        result = format_datetime_for_timezone(utc_dt, 'Asia/Ho_Chi_Minh')
        
        # 2:00 UTC should be 9:00 in Asia/Ho_Chi_Minh (UTC+7)
        assert result == '2024-01-01 09:00'
    
    def test_aware_datetime_with_timezone_to_utc(self):
        """Test converting datetime with timezone to UTC"""
        tz = pytz.timezone('Asia/Ho_Chi_Minh')
        local_dt = tz.localize(datetime(2024, 1, 1, 9, 0))
        result = format_datetime_for_timezone(local_dt, 'UTC')
        
        # 9:00 Asia/Ho_Chi_Minh should be 2:00 UTC
        assert result == '2024-01-01 02:00'
    
    def test_edge_of_day_23_59(self):
        """Test formatting datetime at 23:59"""
        dt = datetime(2024, 1, 1, 23, 59)
        result = format_datetime_for_timezone(dt, 'UTC')
        
        assert result == '2024-01-01 23:59'
    
    def test_edge_of_day_00_00(self):
        """Test formatting datetime at 00:00"""
        dt = datetime(2024, 1, 2, 0, 0)
        result = format_datetime_for_timezone(dt, 'UTC')
        
        assert result == '2024-01-02 00:00'
    
    def test_timezone_conversion_multiple_timezones(self):
        """Test conversion across multiple timezones"""
        utc_dt = pytz.UTC.localize(datetime(2024, 1, 1, 12, 0))
        
        # Test multiple timezone conversions
        asia_result = format_datetime_for_timezone(utc_dt, 'Asia/Ho_Chi_Minh')
        assert '19:00' in asia_result  # UTC+7
        
        london_result = format_datetime_for_timezone(utc_dt, 'Europe/London')
        assert '12:00' in london_result  # UTC+0 in winter
        
        ny_result = format_datetime_for_timezone(utc_dt, 'America/New_York')
        assert '07:00' in ny_result  # UTC-5 in winter
    
    def test_date_crossing_during_conversion(self):
        """Test date change during timezone conversion"""
        # 23:00 UTC on Jan 1
        utc_dt = pytz.UTC.localize(datetime(2024, 1, 1, 23, 0))
        result = format_datetime_for_timezone(utc_dt, 'Asia/Ho_Chi_Minh')
        
        # Should be 06:00 on Jan 2 in Asia/Ho_Chi_Minh
        assert '2024-01-02' in result
        assert '06:00' in result
