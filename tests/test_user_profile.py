"""
Unit tests for user_profile.py
Tests for UserProfile model methods including token generation and validation
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch

from meetings.user_profile import UserProfile


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_user(db):
    """Create a test user with profile"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


# =============================================================================
# UserProfile Token Generation Tests
# =============================================================================

class TestGenerateVerificationToken:
    """Tests for UserProfile.generate_verification_token() method"""
    
    def test_first_generation(self, test_user):
        """Test that token is generated on first call"""
        profile = test_user.profile
        
        assert profile.email_verification_token is None
        assert profile.token_created_at is None
        
        token = profile.generate_verification_token()
        
        assert token is not None
        assert len(token) > 0
        assert profile.email_verification_token == token
        assert profile.token_created_at is not None
    
    def test_regeneration(self, test_user):
        """Test that old token is replaced with new one"""
        profile = test_user.profile
        
        first_token = profile.generate_verification_token()
        first_timestamp = profile.token_created_at
        
        # Wait a tiny bit (simulate time passing)
        import time
        time.sleep(0.01)
        
        second_token = profile.generate_verification_token()
        
        assert second_token != first_token
        assert profile.email_verification_token == second_token
        assert profile.token_created_at > first_timestamp
    
    def test_token_uniqueness(self, test_user):
        """Test that each call generates a different token"""
        profile = test_user.profile
        
        token1 = profile.generate_verification_token()
        profile.email_verification_token = None  # Reset
        token2 = profile.generate_verification_token()
        
        assert token1 != token2


class TestIsVerificationTokenValid:
    """Tests for UserProfile.is_verification_token_valid() method"""
    
    def test_just_created(self, test_user):
        """Test that just-created token is valid"""
        profile = test_user.profile
        profile.generate_verification_token()
        
        assert profile.is_verification_token_valid() is True
    
    @pytest.mark.parametrize("hours_offset,minutes_offset,expiry_hours,expected_valid,scenario", [
        (0, 0, 24, True, "Just created"),
        (23, 59, 24, True, "23h 59m old (24h expiry)"),
        (24, 1, 24, False, "24h 1m old (24h expiry)"),
        (48, 0, 24, False, "48h old (well expired)"),
        (0, 59, 1, True, "59m old (1h expiry)"),
        (1, 1, 1, False, "1h 1m old (1h expiry)"),
        (13, 0, 12, False, "13h old (12h expiry)"),
    ])
    def test_token_expiry(self, test_user, settings, hours_offset, minutes_offset, 
                         expiry_hours, expected_valid, scenario):
        """Test various token expiry scenarios"""
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = expiry_hours
        
        profile = test_user.profile
        profile.email_verification_token = 'test_token'
        profile.token_created_at = timezone.now() - timedelta(hours=hours_offset, minutes=minutes_offset)
        profile.save()
        
        assert profile.is_verification_token_valid() == expected_valid, f"Failed: {scenario}"
    
    def test_no_token_created_at(self, test_user):
        """Test that None token_created_at returns False"""
        profile = test_user.profile
        profile.email_verification_token = 'test_token'
        profile.token_created_at = None
        profile.save()
        
        assert profile.is_verification_token_valid() is False


class TestVerifyEmail:
    """Tests for UserProfile.verify_email() method"""
    
    def test_unverified_to_verified(self, test_user):
        """Test that unverified profile becomes verified"""
        profile = test_user.profile
        profile.email_verified = False
        profile.email_verification_token = 'test_token'
        profile.save()
        
        profile.verify_email()
        
        assert profile.email_verified is True
        assert profile.email_verification_token is None
    
    def test_already_verified(self, test_user):
        """Test that already verified profile stays verified"""
        profile = test_user.profile
        profile.email_verified = True
        profile.email_verification_token = 'test_token'
        profile.save()
        
        profile.verify_email()
        
        assert profile.email_verified is True
        assert profile.email_verification_token is None
    
    def test_token_cleared(self, test_user):
        """Test that verification token is cleared"""
        profile = test_user.profile
        profile.email_verification_token = 'test_token'
        profile.save()
        
        assert profile.email_verification_token == 'test_token'
        profile.verify_email()
        assert profile.email_verification_token is None


# =============================================================================
# Password Reset Token Tests
# =============================================================================

class TestGeneratePasswordResetToken:
    """Tests for UserProfile.generate_password_reset_token() method"""
    
    def test_first_generation(self, test_user):
        """Test that token is generated on first call"""
        profile = test_user.profile
        
        assert profile.password_reset_token is None
        assert profile.password_reset_token_created_at is None
        
        token = profile.generate_password_reset_token()
        
        assert token is not None
        assert len(token) > 0
        assert profile.password_reset_token == token
        assert profile.password_reset_token_created_at is not None
    
    def test_regeneration_multiple_requests(self, test_user):
        """Test that old token is replaced when user requests reset multiple times"""
        profile = test_user.profile
        
        first_token = profile.generate_password_reset_token()
        first_timestamp = profile.password_reset_token_created_at
        
        # Wait a tiny bit (simulate time passing)
        import time
        time.sleep(0.01)
        
        second_token = profile.generate_password_reset_token()
        
        assert second_token != first_token
        assert profile.password_reset_token == second_token
        assert profile.password_reset_token_created_at > first_timestamp
    
    def test_token_uniqueness(self, test_user):
        """Test that each call generates a different token"""
        profile = test_user.profile
        
        token1 = profile.generate_password_reset_token()
        profile.password_reset_token = None  # Reset
        token2 = profile.generate_password_reset_token()
        
        assert token1 != token2


class TestIsPasswordResetTokenValid:
    """Tests for UserProfile.is_password_reset_token_valid() method"""
    
    def test_just_created(self, test_user):
        """Test that just-created token is valid"""
        profile = test_user.profile
        profile.generate_password_reset_token()
        
        assert profile.is_password_reset_token_valid() is True
    
    @pytest.mark.parametrize("hours_offset,minutes_offset,expiry_hours,expected_valid,scenario", [
        (0, 0, 1, True, "Just created (1h expiry)"),
        (0, 59, 1, True, "59m old (1h expiry)"),
        (1, 1, 1, False, "1h 1m old (1h expiry)"),
        (24, 0, 1, False, "24h old (well expired, 1h expiry)"),
        (3, 0, 2, False, "3h old (2h expiry)"),
    ])
    def test_token_expiry(self, test_user, settings, hours_offset, minutes_offset, 
                         expiry_hours, expected_valid, scenario):
        """Test various token expiry scenarios"""
        settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS = expiry_hours
        
        profile = test_user.profile
        profile.password_reset_token = 'test_token'
        profile.password_reset_token_created_at = timezone.now() - timedelta(hours=hours_offset, minutes=minutes_offset)
        profile.save()
        
        assert profile.is_password_reset_token_valid() == expected_valid, f"Failed: {scenario}"
    
    def test_no_token_created_at(self, test_user):
        """Test that None token_created_at returns False"""
        profile = test_user.profile
        profile.password_reset_token = 'test_token'
        profile.password_reset_token_created_at = None
        profile.save()
        
        assert profile.is_password_reset_token_valid() is False


class TestClearPasswordResetToken:
    """Tests for UserProfile.clear_password_reset_token() method"""
    
    def test_token_exists(self, test_user):
        """Test clearing existing token"""
        profile = test_user.profile
        profile.password_reset_token = 'test_token'
        profile.password_reset_token_created_at = timezone.now()
        profile.save()
        
        assert profile.password_reset_token == 'test_token'
        
        profile.clear_password_reset_token()
        
        assert profile.password_reset_token is None
        assert profile.password_reset_token_created_at is None
    
    def test_no_token(self, test_user):
        """Test clearing when no token exists (should not error)"""
        profile = test_user.profile
        profile.password_reset_token = None
        profile.save()
        
        # Should not raise error
        profile.clear_password_reset_token()
        
        assert profile.password_reset_token is None
    
    def test_already_cleared(self, test_user):
        """Test calling clear twice (should not error)"""
        profile = test_user.profile
        profile.password_reset_token = 'test_token'
        profile.save()
        
        profile.clear_password_reset_token()
        assert profile.password_reset_token is None
        
        # Call again - should not error
        profile.clear_password_reset_token()
        assert profile.password_reset_token is None
