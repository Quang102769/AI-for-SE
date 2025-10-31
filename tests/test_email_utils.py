"""
Unit tests for email_utils.py
Tests for email sending functions with mocked Resend API
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from meetings.email_utils import (
    send_email_via_resend,
    send_verification_email,
    send_meeting_invitation_email,
    send_meeting_locked_notification,
    send_password_reset_email
)
from meetings.models import MeetingRequest, Participant, SuggestedSlot
from datetime import date, time


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_email_success():
    """Mock successful email sending"""
    with patch('meetings.email_utils.render_to_string') as mock_render, \
         patch('meetings.email_utils.send_email_via_resend') as mock_send:
        mock_render.return_value = '<p>Test email</p>'
        mock_send.return_value = True
        yield {'render': mock_render, 'send': mock_send}


@pytest.fixture
def mock_email_failure():
    """Mock failed email sending"""
    with patch('meetings.email_utils.render_to_string') as mock_render, \
         patch('meetings.email_utils.send_email_via_resend') as mock_send:
        mock_render.return_value = '<p>Test email</p>'
        mock_send.return_value = False
        yield {'render': mock_render, 'send': mock_send}


@pytest.fixture
def mock_template_error():
    """Mock template rendering error"""
    with patch('meetings.email_utils.render_to_string') as mock_render, \
         patch('meetings.email_utils.send_email_via_resend') as mock_send:
        mock_render.side_effect = Exception('Template error')
        yield {'render': mock_render, 'send': mock_send}


@pytest.fixture
def test_user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


# =============================================================================
# send_email_via_resend Tests
# =============================================================================

class TestSendEmailViaResend:
    """Tests for send_email_via_resend() function"""
    
    @patch('meetings.email_utils.settings')
    def test_api_key_not_configured(self, mock_settings):
        """Test behavior when API key is not configured"""
        mock_settings.RESEND_API_KEY = None
        
        result = send_email_via_resend(
            to_email='user@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert result is False


# =============================================================================
# send_verification_email Tests
# =============================================================================

class TestSendVerificationEmail:
    """Tests for send_verification_email() function"""
    
    def test_valid_user(self, mock_email_success, test_user):
        """Test sending verification email to valid user"""
        result = send_verification_email(test_user, 'http://example.com/verify/token123')
        
        assert result is True
        mock_email_success['render'].assert_called_once()
        mock_email_success['send'].assert_called_once_with(
            to_email='test@example.com',
            subject='Xác thực email của bạn - TimeWeave',
            html_content='<p>Test email</p>'
        )
    
    def test_template_rendering_error(self, mock_template_error, test_user):
        """Test handling of template rendering error"""
        with pytest.raises(Exception):
            send_verification_email(test_user, 'http://example.com/verify/token123')
    
    def test_send_email_fails(self, mock_email_failure, test_user):
        """Test when send_email_via_resend returns False"""
        result = send_verification_email(test_user, 'http://example.com/verify/token123')
        assert result is False


# =============================================================================
# send_meeting_invitation_email Tests
# =============================================================================

class TestSendMeetingInvitationEmail:
    """Tests for send_meeting_invitation_email() function"""
    
    def test_participant_with_email(self, mock_email_success, create_meeting_request, create_participant):
        """Test sending invitation to participant with email"""
        meeting = create_meeting_request(title='Test Meeting')
        participant = create_participant(meeting, email='user@example.com')
        
        result = send_meeting_invitation_email(
            participant,
            meeting,
            'http://example.com/respond/123'
        )
        
        assert result is True
        mock_email_success['send'].assert_called_once_with(
            to_email='user@example.com',
            subject='Mời tham gia cuộc họp: Test Meeting',
            html_content='<p>Test email</p>'
        )
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_participant_without_email(self, mock_send, create_meeting_request, create_participant):
        """Test sending invitation to participant without email"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email=None)
        
        result = send_meeting_invitation_email(
            participant,
            meeting,
            'http://example.com/respond/123'
        )
        
        assert result is False
        mock_send.assert_not_called()
    
    def test_template_rendering_error(self, mock_template_error, create_meeting_request, create_participant):
        """Test handling of template rendering error"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email='user@example.com')
        
        with pytest.raises(Exception):
            send_meeting_invitation_email(
                participant,
                meeting,
                'http://example.com/respond/123'
            )
    
    def test_send_email_fails(self, mock_email_failure, create_meeting_request, create_participant):
        """Test when send_email_via_resend returns False"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email='user@example.com')
        
        result = send_meeting_invitation_email(
            participant,
            meeting,
            'http://example.com/respond/123'
        )
        
        assert result is False


# =============================================================================
# send_meeting_locked_notification Tests
# =============================================================================

class TestSendMeetingLockedNotification:
    """Tests for send_meeting_locked_notification() function"""
    
    def test_participant_with_email(self, mock_email_success, create_meeting_request, 
                                   create_participant, create_suggested_slot, create_utc_datetime):
        """Test sending notification to participant with email"""
        meeting = create_meeting_request(title='Test Meeting')
        participant = create_participant(meeting, email='user@example.com')
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        locked_slot = create_suggested_slot(meeting, start, end, available_count=5, total_participants=5)
        
        result = send_meeting_locked_notification(
            participant,
            meeting,
            locked_slot
        )
        
        assert result is True
        mock_email_success['send'].assert_called_once()
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_participant_without_email(self, mock_send, create_meeting_request, 
                                      create_participant, create_suggested_slot, create_utc_datetime):
        """Test notification to participant without email"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email=None)
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        locked_slot = create_suggested_slot(meeting, start, end)
        
        result = send_meeting_locked_notification(
            participant,
            meeting,
            locked_slot
        )
        
        assert result is False
        mock_send.assert_not_called()
    
    def test_template_rendering_error(self, mock_template_error, create_meeting_request, 
                                     create_participant, create_suggested_slot, create_utc_datetime):
        """Test handling of template rendering error"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email='user@example.com')
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        locked_slot = create_suggested_slot(meeting, start, end)
        
        with pytest.raises(Exception):
            send_meeting_locked_notification(participant, meeting, locked_slot)
    
    def test_send_email_fails(self, mock_email_failure, create_meeting_request, 
                             create_participant, create_suggested_slot, create_utc_datetime):
        """Test when send_email_via_resend returns False"""
        meeting = create_meeting_request()
        participant = create_participant(meeting, email='user@example.com')
        start = create_utc_datetime(2024, 1, 1, 9, 0)
        end = create_utc_datetime(2024, 1, 1, 10, 0)
        locked_slot = create_suggested_slot(meeting, start, end)
        
        result = send_meeting_locked_notification(participant, meeting, locked_slot)
        
        assert result is False


# =============================================================================
# send_password_reset_email Tests
# =============================================================================

class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email() function"""
    
    def test_valid_user(self, mock_email_success, test_user):
        """Test sending password reset email to valid user"""
        result = send_password_reset_email(test_user, 'http://example.com/reset/token123')
        
        assert result is True
        mock_email_success['send'].assert_called_once_with(
            to_email='test@example.com',
            subject='Đặt lại mật khẩu - TimeWeave',
            html_content='<p>Test email</p>'
        )
    
    def test_template_rendering_error(self, mock_template_error, test_user):
        """Test handling of template rendering error"""
        with pytest.raises(Exception):
            send_password_reset_email(test_user, 'http://example.com/reset/token123')
    
    def test_send_email_fails(self, mock_email_failure, test_user):
        """Test when send_email_via_resend returns False"""
        result = send_password_reset_email(test_user, 'http://example.com/reset/token123')
        assert result is False
