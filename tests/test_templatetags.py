"""
Unit tests for template tags and filters
Tests custom template filters in meeting_filters.py
"""
import pytest
from meetings.templatetags.meeting_filters import get_item, format_date_header


class TestGetItem:
    """Test cases for get_item template filter"""
    
    def test_dictionary_is_none(self):
        """Test get_item when dictionary is None"""
        result = get_item(None, 'test')
        assert result is None
    
    def test_key_exists(self):
        """Test get_item when key exists in dictionary"""
        dictionary = {'test': 'value', 'other': 'data'}
        result = get_item(dictionary, 'test')
        assert result == 'value'
    
    def test_key_doesnt_exist(self):
        """Test get_item when key doesn't exist"""
        dictionary = {'other': 'value'}
        result = get_item(dictionary, 'test')
        assert result is None
    
    def test_empty_dictionary(self):
        """Test get_item with empty dictionary"""
        dictionary = {}
        result = get_item(dictionary, 'test')
        assert result is None
    
    def test_non_string_keys(self):
        """Test get_item with non-string keys"""
        dictionary = {1: 'value', 2: 'other'}
        result = get_item(dictionary, 1)
        assert result == 'value'
    
    def test_nested_values(self):
        """Test get_item with nested dictionary values"""
        dictionary = {'level1': {'level2': 'nested_value'}}
        result = get_item(dictionary, 'level1')
        assert result == {'level2': 'nested_value'}


class TestFormatDateHeader:
    """Test cases for format_date_header template filter"""
    
    def test_monday(self):
        """Test formatting Monday"""
        # 2024-01-01 is a Monday
        result = format_date_header('2024-01-01')
        assert result == 'T2 1/1'
    
    def test_tuesday(self):
        """Test formatting Tuesday"""
        # 2024-01-02 is a Tuesday
        result = format_date_header('2024-01-02')
        assert result == 'T3 2/1'
    
    def test_wednesday(self):
        """Test formatting Wednesday"""
        # 2024-01-03 is a Wednesday
        result = format_date_header('2024-01-03')
        assert result == 'T4 3/1'
    
    def test_thursday(self):
        """Test formatting Thursday"""
        # 2024-01-04 is a Thursday
        result = format_date_header('2024-01-04')
        assert result == 'T5 4/1'
    
    def test_friday(self):
        """Test formatting Friday"""
        # 2024-01-05 is a Friday
        result = format_date_header('2024-01-05')
        assert result == 'T6 5/1'
    
    def test_saturday(self):
        """Test formatting Saturday"""
        # 2024-01-06 is a Saturday
        result = format_date_header('2024-01-06')
        assert result == 'T7 6/1'
    
    def test_sunday(self):
        """Test formatting Sunday"""
        # 2024-01-07 is a Sunday
        result = format_date_header('2024-01-07')
        assert result == 'CN 7/1'
    
    def test_invalid_date_format(self):
        """Test formatting with invalid date format"""
        result = format_date_header('invalid-date')
        assert result == 'invalid-date'
    
    def test_different_months(self):
        """Test formatting dates in different months"""
        # December 25th (Thursday)
        result = format_date_header('2024-12-25')
        assert result == 'T4 25/12'
    
    def test_edge_of_month(self):
        """Test formatting end of month"""
        # January 31st (Wednesday)
        result = format_date_header('2024-01-31')
        assert result == 'T4 31/1'
    
    def test_leap_year_date(self):
        """Test formatting leap year date"""
        # February 29th, 2024 (Thursday)
        result = format_date_header('2024-02-29')
        assert result == 'T5 29/2'
    
    @pytest.mark.parametrize('date_str,expected', [
        ('2024-01-01', 'T2 1/1'),
        ('2024-01-02', 'T3 2/1'),
        ('2024-01-03', 'T4 3/1'),
        ('2024-01-04', 'T5 4/1'),
        ('2024-01-05', 'T6 5/1'),
        ('2024-01-06', 'T7 6/1'),
        ('2024-01-07', 'CN 7/1'),
    ])
    def test_all_weekdays_parametrized(self, date_str, expected):
        """Parametrized test for all days of the week"""
        result = format_date_header(date_str)
        assert result == expected
