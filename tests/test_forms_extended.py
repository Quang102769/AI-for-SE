"""
Extended unit tests for forms.py
Tests form validation and cleaning methods
"""
import pytest
from datetime import date, time, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from meetings.forms import (
    UserRegistrationForm,
    MeetingRequestForm,
    BusySlotForm
)
from meetings.models import MeetingRequest
import pytz


@pytest.mark.django_db
class TestUserRegistrationFormCleanEmail:
    """Test cases for UserRegistrationForm.clean_email method"""
    
    def test_unique_email_valid(self):
        """Test clean_email with unique email"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        
        assert form.is_valid()
        assert form.cleaned_data['email'] == 'newuser@example.com'
    
    def test_duplicate_email_invalid(self):
        """Test clean_email with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass'
        )
        
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_empty_email(self):
        """Test clean_email with empty email"""
        form_data = {
            'username': 'newuser',
            'email': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        
        assert not form.is_valid()


@pytest.mark.django_db
class TestMeetingRequestFormClean:
    """Test cases for MeetingRequestForm.clean method"""
    
    def test_start_date_in_past(self):
        """Test clean with start date in past"""
        yesterday = (timezone.now() - timedelta(days=1)).date()
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': yesterday,
            'date_range_end': tomorrow,
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
        assert 'Ngày bắt đầu không được ở quá khứ' in str(form.errors)
    
    def test_end_date_in_past(self):
        """Test clean with end date in past"""
        yesterday = (timezone.now() - timedelta(days=1)).date()
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': tomorrow,
            'date_range_end': yesterday,
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
    
    def test_end_date_before_start_date(self):
        """Test clean with end date before start date"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today + timedelta(days=10),
            'date_range_end': today + timedelta(days=5),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
        assert 'Ngày kết thúc phải sau ngày bắt đầu' in str(form.errors)
    
    def test_date_range_exceeds_90_days(self):
        """Test clean with date range > 90 days"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=91),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
        assert '90 ngày' in str(form.errors)
    
    def test_response_deadline_in_past(self):
        """Test clean with response deadline in past"""
        today = timezone.now().date()
        past_deadline = timezone.now() - timedelta(hours=1)
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=1),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'response_deadline': past_deadline,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
        assert 'Hạn chót trả lời không được ở quá khứ' in str(form.errors)
    
    def test_work_end_before_work_start(self):
        """Test clean with work end before work start"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=1),
            'work_hours_start': time(17, 0),
            'work_hours_end': time(9, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert not form.is_valid()
        assert 'Giờ kết thúc phải sau giờ bắt đầu' in str(form.errors)
    
    def test_valid_configuration(self):
        """Test clean with valid configuration"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=1),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert form.is_valid()
    
    def test_today_as_start_date_valid(self):
        """Test clean with today as start date (valid)"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=1),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert form.is_valid()
    
    def test_exactly_90_days_range(self):
        """Test clean with exactly 90 days range"""
        today = timezone.now().date()
        
        form_data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': today,
            'date_range_end': today + timedelta(days=90),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': 'test@example.com'
        }
        form = MeetingRequestForm(data=form_data)
        
        assert form.is_valid()


@pytest.mark.django_db
class TestBusySlotFormClean:
    """Test cases for BusySlotForm.clean method"""
    
    def test_end_after_start_valid(self):
        """Test clean with end after start (valid)"""
        form_data = {
            'start_time': timezone.make_aware(
                timezone.datetime(2024, 1, 1, 9, 0)
            ),
            'end_time': timezone.make_aware(
                timezone.datetime(2024, 1, 1, 10, 0)
            ),
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        
        assert form.is_valid()
    
    def test_end_before_start_invalid(self):
        """Test clean with end before start (invalid)"""
        form_data = {
            'start_time': timezone.make_aware(
                timezone.datetime(2024, 1, 1, 10, 0)
            ),
            'end_time': timezone.make_aware(
                timezone.datetime(2024, 1, 1, 9, 0)
            ),
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        
        assert not form.is_valid()
        assert 'Thời gian kết thúc phải sau thời gian bắt đầu' in str(form.errors)
    
    def test_end_equals_start_invalid(self):
        """Test clean with end equals start (invalid)"""
        same_time = timezone.make_aware(
            timezone.datetime(2024, 1, 1, 9, 0)
        )
        form_data = {
            'start_time': same_time,
            'end_time': same_time,
            'description': 'Busy'
        }
        form = BusySlotForm(data=form_data)
        
        assert not form.is_valid()
