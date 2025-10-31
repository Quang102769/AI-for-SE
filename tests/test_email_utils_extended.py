"""
Extended unit tests for email_utils.py
Tests email sending functionality using Resend API
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from meetings.email_utils import (
    send_email_via_resend,
    send_verification_email,
    send_meeting_invitation_email,
    send_meeting_locked_notification,
    send_password_reset_email
)
from meetings.models import MeetingRequest, Participant, SuggestedSlot
from datetime import datetime, date, time
import pytz


@pytest.mark.django_db
class TestSendEmailViaResend:
    """Test cases for send_email_via_resend function"""
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', 'test-api-key')
    @patch('meetings.email_utils.settings.DEFAULT_FROM_EMAIL', 'from@test.com')
    def test_successful_email_send(self):
        """Test successful email send via Resend"""
        # Since resend is imported inside the function, we need to mock it there
        with patch('resend.Emails') as mock_emails:
            mock_emails.send.return_value = {'id': 'email-123'}
            
            result = send_email_via_resend(
                to_email='test@example.com',
                subject='Test Subject',
                html_content='<p>Test Content</p>'
            )
            
            assert result is True
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', None)
    def test_no_api_key_configured(self, caplog):
        """Test when no API key is configured"""
        result = send_email_via_resend(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert result is False
        assert 'RESEND_API_KEY not configured' in caplog.text
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', 'test-api-key')
    @patch('meetings.email_utils.settings.DEFAULT_FROM_EMAIL', 'from@test.com')
    def test_multiple_recipients(self):
        """Test sending email to multiple recipients"""
        with patch('resend.Emails') as mock_emails:
            mock_emails.send.return_value = {'id': 'email-123'}
            
            result = send_email_via_resend(
                to_email=['test1@example.com', 'test2@example.com'],
                subject='Test',
                html_content='<p>Test</p>'
            )
            
            assert result is True
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', 'test-api-key')
    def test_empty_subject(self):
        """Test sending email with empty subject"""
        with patch('resend.Emails') as mock_emails:
            mock_emails.send.return_value = {'id': 'email-123'}
            
            result = send_email_via_resend(
                to_email='test@example.com',
                subject='',
                html_content='<p>Test</p>'
            )
            
            # Should still send
            assert result is True
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', 'test-api-key')
    def test_empty_content(self):
        """Test sending email with empty content"""
        with patch('resend.Emails') as mock_emails:
            mock_emails.send.return_value = {'id': 'email-123'}
            
            result = send_email_via_resend(
                to_email='test@example.com',
                subject='Test',
                html_content=''
            )
            
            # Should still send
            assert result is True
    
    @patch('meetings.email_utils.settings.RESEND_API_KEY', 'test-api-key')
    def test_resend_api_exception(self, caplog):
        """Test handling Resend API exception"""
        with patch('resend.Emails') as mock_emails:
            mock_emails.send.side_effect = Exception('API Error')
            
            result = send_email_via_resend(
                to_email='test@example.com',
                subject='Test',
                html_content='<p>Test</p>'
            )
            
            assert result is False
            assert 'Failed to send email' in caplog.text


@pytest.mark.django_db
class TestSendVerificationEmail:
    """Test cases for send_verification_email function"""
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_successful_verification_email(self, mock_send):
        """Test successful verification email send"""
        mock_send.return_value = True
        
        user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        
        result = send_verification_email(
            user=user,
            verification_url='http://example.com/verify/token123'
        )
        
        assert result is True
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs['to_email'] == 'test@example.com'
        assert 'Xác thực email' in kwargs['subject']
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_user_with_no_email(self, mock_send):
        """Test verification email when user has no email"""
        user = User.objects.create(
            username='testuser',
            email=''
        )
        
        result = send_verification_email(
            user=user,
            verification_url='http://example.com/verify/token'
        )
        
        # Should attempt to send but may fail
        assert mock_send.called


@pytest.mark.django_db
class TestSendMeetingInvitationEmail:
    """Test cases for send_meeting_invitation_email function"""
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_successful_invitation(self, mock_send, create_meeting_request):
        """Test successful meeting invitation"""
        mock_send.return_value = True
        
        meeting = create_meeting_request(title='Test Meeting')
        participant = Participant.objects.create(
            meeting_request=meeting,
            email='participant@example.com',
            name='Test Participant'
        )
        
        result = send_meeting_invitation_email(
            participant=participant,
            meeting_request=meeting,
            respond_url='http://example.com/respond'
        )
        
        assert result is True
        mock_send.assert_called_once()
    
    def test_participant_without_email(self, create_meeting_request):
        """Test invitation when participant has no email"""
        meeting = create_meeting_request()
        participant = Participant.objects.create(
            meeting_request=meeting,
            email=None,
            name='Test Participant'
        )
        
        result = send_meeting_invitation_email(
            participant=participant,
            meeting_request=meeting,
            respond_url='http://example.com/respond'
        )
        
        assert result is False
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_empty_respond_url(self, mock_send, create_meeting_request):
        """Test invitation with empty respond URL"""
        mock_send.return_value = True
        
        meeting = create_meeting_request()
        participant = Participant.objects.create(
            meeting_request=meeting,
            email='participant@example.com',
            name='Test Participant'
        )
        
        result = send_meeting_invitation_email(
            participant=participant,
            meeting_request=meeting,
            respond_url=''
        )
        
        # Should still send
        assert result is True


@pytest.mark.django_db
class TestSendMeetingLockedNotification:
    """Test cases for send_meeting_locked_notification function"""
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_successful_notification(self, mock_send, create_meeting_request, create_utc_datetime):
        """Test successful meeting locked notification"""
        mock_send.return_value = True
        
        meeting = create_meeting_request()
        participant = Participant.objects.create(
            meeting_request=meeting,
            email='participant@example.com',
            name='Test Participant'
        )
        locked_slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            available_count=5,
            total_participants=10,
            is_locked=True
        )
        
        result = send_meeting_locked_notification(
            participant=participant,
            meeting_request=meeting,
            locked_slot=locked_slot
        )
        
        assert result is True
        mock_send.assert_called_once()
    
    def test_participant_without_email(self, create_meeting_request, create_utc_datetime):
        """Test notification when participant has no email"""
        meeting = create_meeting_request()
        participant = Participant.objects.create(
            meeting_request=meeting,
            email=None,
            name='Test Participant'
        )
        locked_slot = SuggestedSlot.objects.create(
            meeting_request=meeting,
            start_time=create_utc_datetime(2024, 1, 1, 9, 0),
            end_time=create_utc_datetime(2024, 1, 1, 10, 0),
            is_locked=True
        )
        
        result = send_meeting_locked_notification(
            participant=participant,
            meeting_request=meeting,
            locked_slot=locked_slot
        )
        
        assert result is False


@pytest.mark.django_db
class TestSendPasswordResetEmail:
    """Test cases for send_password_reset_email function"""
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_successful_reset_email(self, mock_send):
        """Test successful password reset email"""
        mock_send.return_value = True
        
        user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        
        result = send_password_reset_email(
            user=user,
            reset_url='http://example.com/reset/token123'
        )
        
        assert result is True
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs['to_email'] == 'test@example.com'
        assert 'mật khẩu' in kwargs['subject'].lower()
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_user_with_no_email(self, mock_send):
        """Test password reset when user has no email"""
        user = User.objects.create(
            username='testuser',
            email=''
        )
        
        result = send_password_reset_email(
            user=user,
            reset_url='http://example.com/reset/token'
        )
        
        # Should attempt to send
        assert mock_send.called
    
    @patch('meetings.email_utils.send_email_via_resend')
    def test_invalid_reset_url(self, mock_send):
        """Test password reset with invalid URL"""
        mock_send.return_value = True
        
        user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        
        result = send_password_reset_email(
            user=user,
            reset_url=''
        )
        
        # Should still send but URL will be empty
        assert result is True
