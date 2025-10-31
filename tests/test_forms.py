"""
Unit tests for forms.py
Tests for form validation including UserRegistrationForm, MeetingRequestForm, and BusySlotForm
"""
import pytest
from datetime import date, time, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from meetings.forms import (
    UserRegistrationForm,
    MeetingRequestForm,
    BusySlotForm,
    ParticipantForm
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def base_form_data(test_dates):
    """Base form data with valid defaults for MeetingRequestForm"""
    return {
        'title': 'Test Meeting',
        'duration_minutes': 60,
        'timezone': 'UTC',
        'date_range_start': test_dates['tomorrow'],
        'date_range_end': test_dates['next_week'],
        'work_hours_start': time(9, 0),
        'work_hours_end': time(17, 0),
        'step_size_minutes': 30,
        'work_days_only': True,
        'created_by_email': 'test@example.com'
    }


# =============================================================================
# UserRegistrationForm Tests
# =============================================================================

class TestUserRegistrationFormCleanEmail:
    """Tests for UserRegistrationForm.clean_email() validation"""
    
    def test_unique_email(self, db):
        """Test that unique email passes validation"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        assert form.is_valid()
    
    def test_duplicate_email(self, db):
        """Test that duplicate email raises ValidationError"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        
        # Try to register with same email
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors


# =============================================================================
# MeetingRequestForm Tests
# =============================================================================

class TestMeetingRequestFormClean:
    """Tests for MeetingRequestForm.clean() validation"""
    
    def test_all_valid_fields(self, db, base_form_data):
        """Test that all valid fields pass validation"""
        form_data = base_form_data.copy()
        form_data['description'] = 'Test description'
        
        form = MeetingRequestForm(data=form_data)
        assert form.is_valid()
    
    @pytest.mark.parametrize("start_offset,end_offset,should_be_valid,scenario", [
        (1, 7, True, "Valid future range"),
        (1, 1, False, "Same day range (end must be after start)"),
        (-1, 1, False, "Start in past"),
        (1, -1, False, "End in past"),
        (-2, -1, False, "Both in past"),
        (7, 1, False, "End before start"),
        (1, 100, False, "Range > 90 days"),
    ])
    def test_date_range_validation(self, db, base_form_data, test_dates, 
                                   start_offset, end_offset, should_be_valid, scenario):
        """Test various date range validation scenarios"""
        now = timezone.now()
        form_data = base_form_data.copy()
        form_data['date_range_start'] = (now + timedelta(days=start_offset)).date()
        form_data['date_range_end'] = (now + timedelta(days=end_offset)).date()
        
        form = MeetingRequestForm(data=form_data)
        assert form.is_valid() == should_be_valid, f"Failed: {scenario}"
    
    def test_valid_work_hours(self, db, base_form_data):
        """Test that valid work hours pass validation"""
        form = MeetingRequestForm(data=base_form_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        assert form.is_valid()
    
    def test_invalid_work_hours_end_before_start(self, db, base_form_data):
        """Test that end time before start time raises ValidationError"""
        form_data = base_form_data.copy()
        form_data['date_range_end'] = form_data['date_range_start']
        form_data['work_hours_start'] = time(17, 0)
        form_data['work_hours_end'] = time(9, 0)
        
        form = MeetingRequestForm(data=form_data)
        assert not form.is_valid()
    
    def test_work_hours_equal(self, db, base_form_data):
        """Test that equal work hours raises ValidationError"""
        form_data = base_form_data.copy()
        form_data['date_range_end'] = form_data['date_range_start']
        form_data['work_hours_start'] = time(9, 0)
        form_data['work_hours_end'] = time(9, 0)
        
        form = MeetingRequestForm(data=form_data)
        assert not form.is_valid()
    
    def test_response_deadline_in_past(self, db, base_form_data):
        """Test that response deadline in past raises ValidationError"""
        form_data = base_form_data.copy()
        form_data['response_deadline'] = timezone.now() - timedelta(hours=1)
        
        form = MeetingRequestForm(data=form_data)
        assert not form.is_valid()
    
    def test_response_deadline_in_future(self, db, base_form_data):
        """Test that response deadline in future passes validation"""
        form_data = base_form_data.copy()
        form_data['response_deadline'] = timezone.now() + timedelta(days=2)
        
        form = MeetingRequestForm(data=form_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        assert form.is_valid()
    
    def test_no_response_deadline(self, db, base_form_data):
        """Test that no response deadline passes validation"""
        form = MeetingRequestForm(data=base_form_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        assert form.is_valid()


# =============================================================================
# BusySlotForm Tests
# =============================================================================

class TestBusySlotFormClean:
    """Tests for BusySlotForm.clean() validation"""
    
    def test_valid_time_range(self, db):
        """Test that valid time range passes validation"""
        start = timezone.now() + timedelta(hours=1)
        end = timezone.now() + timedelta(hours=2)
        
        form_data = {
            'start_time': start,
            'end_time': end,
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        assert form.is_valid()
    
    def test_invalid_time_range_end_before_start(self, db):
        """Test that end time before start time raises ValidationError"""
        start = timezone.now() + timedelta(hours=2)
        end = timezone.now() + timedelta(hours=1)
        
        form_data = {
            'start_time': start,
            'end_time': end,
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        assert not form.is_valid()
    
    def test_times_equal(self, db):
        """Test that equal start and end times raise ValidationError"""
        same_time = timezone.now() + timedelta(hours=1)
        
        form_data = {
            'start_time': same_time,
            'end_time': same_time,
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        assert not form.is_valid()
