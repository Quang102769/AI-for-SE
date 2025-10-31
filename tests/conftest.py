"""
Pytest configuration and shared fixtures for testing time slot calculations
"""
import pytest
import pytz
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from meetings.models import MeetingRequest, Participant, BusySlot, SuggestedSlot


@pytest.fixture(scope="session")
def utc():
    """UTC timezone instance (session-scoped for performance)"""
    return pytz.UTC


@pytest.fixture
def create_utc_datetime():
    """Helper to create UTC datetime quickly"""
    def _create(year=2024, month=1, day=1, hour=9, minute=0, second=0):
        return pytz.UTC.localize(datetime(year, month, day, hour, minute, second))
    return _create


@pytest.fixture
def sample_meeting_request(db):
    """
    Create a basic meeting request for testing
    Default: 60-minute meeting, 30-minute steps, Jan 1-2 2024, 9AM-5PM
    """
    return MeetingRequest.objects.create(
        title="Test Meeting",
        description="Test Description",
        duration_minutes=60,
        timezone='UTC',
        date_range_start=date(2024, 1, 1),
        date_range_end=date(2024, 1, 2),
        work_hours_start=time(9, 0),
        work_hours_end=time(17, 0),
        step_size_minutes=30,
        work_days_only=True,
        status='active'
    )


@pytest.fixture
def create_meeting_request(db):
    """
    Factory fixture to create customized meeting requests
    """
    def _create(**kwargs):
        defaults = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'UTC',
            'date_range_start': date(2024, 1, 1),
            'date_range_end': date(2024, 1, 1),
            'work_hours_start': time(9, 0),
            'work_hours_end': time(17, 0),
            'step_size_minutes': 30,
            'work_days_only': True,
            'status': 'active'
        }
        defaults.update(kwargs)
        return MeetingRequest.objects.create(**defaults)
    return _create


@pytest.fixture
def create_participant(db):
    """
    Factory fixture to create participants
    """
    def _create(meeting_request, **kwargs):
        defaults = {
            'name': 'Test Participant',
            'email': f'participant{Participant.objects.count()}@test.com',
            'timezone': 'UTC',
            'has_responded': False
        }
        defaults.update(kwargs)
        return Participant.objects.create(
            meeting_request=meeting_request,
            **defaults
        )
    return _create


@pytest.fixture
def create_busy_slot(db):
    """
    Factory fixture to create busy slots
    """
    def _create(participant, start_time, end_time, **kwargs):
        defaults = {
            'description': 'Busy'
        }
        defaults.update(kwargs)
        return BusySlot.objects.create(
            participant=participant,
            start_time=start_time,
            end_time=end_time,
            **defaults
        )
    return _create


@pytest.fixture
def create_suggested_slot(db):
    """
    Factory fixture to create suggested slots
    """
    def _create(meeting_request, start_time, end_time, **kwargs):
        defaults = {
            'available_count': 0,
            'total_participants': 0
        }
        defaults.update(kwargs)
        return SuggestedSlot.objects.create(
            meeting_request=meeting_request,
            start_time=start_time,
            end_time=end_time,
            **defaults
        )
    return _create


@pytest.fixture
def create_participants_bulk(db):
    """Factory to create multiple participants efficiently using bulk_create"""
    def _create(meeting_request, count, has_responded=True, email_prefix='participant', **kwargs):
        participants = [
            Participant(
                meeting_request=meeting_request,
                has_responded=has_responded,
                email=f'{email_prefix}{i}@test.com',
                name=kwargs.get('name', f'{email_prefix.capitalize()} {i}'),
                timezone=kwargs.get('timezone', 'UTC')
            ) for i in range(count)
        ]
        return Participant.objects.bulk_create(participants)
    return _create


@pytest.fixture
def create_busy_slots_bulk(db):
    """Factory to create multiple busy slots efficiently using bulk_create"""
    def _create(participants, start_time, end_time, **kwargs):
        busy_slots = [
            BusySlot(
                participant=p,
                start_time=start_time,
                end_time=end_time,
                description=kwargs.get('description', 'Busy')
            ) for p in participants
        ]
        return BusySlot.objects.bulk_create(busy_slots)
    return _create


@pytest.fixture
def test_dates():
    """Pre-calculated dates for testing to avoid repeated date calculations"""
    now = timezone.now()
    return {
        'yesterday': (now - timedelta(days=1)).date(),
        'today': now.date(),
        'tomorrow': (now + timedelta(days=1)).date(),
        'next_week': (now + timedelta(days=7)).date(),
        'next_month': (now + timedelta(days=30)).date(),
        'far_future': (now + timedelta(days=100)).date(),
    }



