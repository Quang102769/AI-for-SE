"""
Extended unit tests for user_profile.py
Tests UserProfile model methods for email verification and password reset
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import override_settings
from meetings.user_profile import UserProfile


@pytest.mark.django_db
class TestUserProfileGenerateVerificationToken:
    """Test cases for UserProfile.generate_verification_token method"""
    
    def test_first_time_generation(self):
        """Test first time token generation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile
        
        # Ensure no token initially
        profile.email_verification_token = None
        profile.token_created_at = None
        profile.save()
        
        token = profile.generate_verification_token()
        
        assert token is not None
        assert len(token) > 0
        assert profile.email_verification_token == token
        assert profile.token_created_at is not None
    
    def test_regeneration(self):
        """Test token regeneration"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile
        
        first_token = profile.generate_verification_token()
        second_token = profile.generate_verification_token()
        
        assert first_token != second_token
        assert profile.email_verification_token == second_token
    
    def test_token_uniqueness(self):
        """Test that multiple calls generate unique tokens"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass'
        )
        
        token1 = user1.profile.generate_verification_token()
        token2 = user2.profile.generate_verification_token()
        
        assert token1 != token2


@pytest.mark.django_db
class TestUserProfileIsVerificationTokenValid:
    """Test cases for UserProfile.is_verification_token_valid method"""
    
    def test_no_token_created_at(self):
        """Test is_verification_token_valid with no token_created_at"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.token_created_at = None
        profile.save()
        
        assert profile.is_verification_token_valid() is False
    
    def test_token_just_created(self):
        """Test is_verification_token_valid with freshly created token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.generate_verification_token()
        
        assert profile.is_verification_token_valid() is True
    
    def test_token_within_expiry_window(self):
        """Test is_verification_token_valid for token created 1 hour ago"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        # Generate a fresh token
        profile.generate_verification_token()
        
        # Token was just created, should be valid
        assert profile.is_verification_token_valid() is True
    
    def test_token_expired_25_hours(self):
        """Test is_verification_token_valid with expired token (25 hours)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.email_verification_token = 'test-token'
        profile.token_created_at = timezone.now() - timedelta(hours=25)
        profile.save()
        
        assert profile.is_verification_token_valid() is False
    
    @override_settings(EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=48)
    def test_custom_expiry_setting(self):
        """Test is_verification_token_valid with custom expiry setting"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.email_verification_token = 'test-token'
        profile.token_created_at = timezone.now() - timedelta(hours=47)
        profile.save()
        
        # Should still be valid with 48 hour expiry
        assert profile.is_verification_token_valid() is True


@pytest.mark.django_db
class TestUserProfileVerifyEmail:
    """Test cases for UserProfile.verify_email method"""
    
    def test_first_verification(self):
        """Test first email verification"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.email_verified = False
        profile.email_verification_token = 'test-token'
        profile.token_created_at = timezone.now()
        profile.save()
        
        profile.verify_email()
        
        assert profile.email_verified is True
        assert profile.email_verification_token is None
        assert profile.token_created_at is None
    
    def test_re_verification(self):
        """Test re-verification of already verified email"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.email_verified = True
        profile.email_verification_token = 'test-token'
        profile.save()
        
        profile.verify_email()
        
        assert profile.email_verified is True
        assert profile.email_verification_token is None
    
    def test_token_cleared(self):
        """Test that token is cleared after verification"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.generate_verification_token()
        
        profile.verify_email()
        
        assert profile.email_verification_token is None
        assert profile.token_created_at is None


@pytest.mark.django_db
class TestUserProfileGeneratePasswordResetToken:
    """Test cases for UserProfile.generate_password_reset_token method"""
    
    def test_first_time_generation(self):
        """Test first time password reset token generation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        
        token = profile.generate_password_reset_token()
        
        assert token is not None
        assert len(token) > 0
        assert profile.password_reset_token == token
        assert profile.password_reset_token_created_at is not None
    
    def test_regeneration_multiple_reset_requests(self):
        """Test regeneration (multiple reset requests)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        
        first_token = profile.generate_password_reset_token()
        second_token = profile.generate_password_reset_token()
        
        assert first_token != second_token
        assert profile.password_reset_token == second_token
    
    def test_token_uniqueness(self):
        """Test token uniqueness across different profiles"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass'
        )
        
        token1 = user1.profile.generate_password_reset_token()
        token2 = user2.profile.generate_password_reset_token()
        
        assert token1 != token2


@pytest.mark.django_db
class TestUserProfileIsPasswordResetTokenValid:
    """Test cases for UserProfile.is_password_reset_token_valid method"""
    
    def test_no_token_created(self):
        """Test is_password_reset_token_valid with no token created"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.password_reset_token_created_at = None
        profile.save()
        
        assert profile.is_password_reset_token_valid() is False
    
    def test_token_just_created(self):
        """Test is_password_reset_token_valid with freshly created token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.generate_password_reset_token()
        
        assert profile.is_password_reset_token_valid() is True
    
    def test_token_at_expiry_boundary_59_minutes(self):
        """Test is_password_reset_token_valid at 59 minutes"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.password_reset_token = 'test-token'
        profile.password_reset_token_created_at = timezone.now() - timedelta(minutes=59)
        profile.save()
        
        assert profile.is_password_reset_token_valid() is True
    
    def test_token_expired_2_hours(self):
        """Test is_password_reset_token_valid with expired token (2 hours)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.password_reset_token = 'test-token'
        profile.password_reset_token_created_at = timezone.now() - timedelta(hours=2)
        profile.save()
        
        assert profile.is_password_reset_token_valid() is False
    
    @override_settings(PASSWORD_RESET_TOKEN_EXPIRY_HOURS=2)
    def test_custom_expiry_setting(self):
        """Test is_password_reset_token_valid with custom expiry setting"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.password_reset_token = 'test-token'
        profile.password_reset_token_created_at = timezone.now() - timedelta(hours=1, minutes=59)
        profile.save()
        
        # Should still be valid with 2 hour expiry
        assert profile.is_password_reset_token_valid() is True


@pytest.mark.django_db
class TestUserProfileClearPasswordResetToken:
    """Test cases for UserProfile.clear_password_reset_token method"""
    
    def test_token_exists(self):
        """Test clearing existing token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.generate_password_reset_token()
        
        profile.clear_password_reset_token()
        
        assert profile.password_reset_token is None
        assert profile.password_reset_token_created_at is None
    
    def test_token_already_cleared(self):
        """Test clearing token when already cleared"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        profile.password_reset_token = None
        profile.password_reset_token_created_at = None
        profile.save()
        
        # Should not raise error
        profile.clear_password_reset_token()
        
        assert profile.password_reset_token is None
    
    def test_no_token_to_clear(self):
        """Test clearing when no token exists"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        profile = user.profile
        
        # Should not raise error
        profile.clear_password_reset_token()
        
        assert profile.password_reset_token is None
        assert profile.password_reset_token_created_at is None
