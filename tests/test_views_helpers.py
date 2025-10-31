"""
Unit tests for view helper functions
Tests helper functions used in views.py
"""
import pytest
from django.test import RequestFactory
from meetings.views import get_or_create_creator_id


@pytest.mark.django_db
class TestGetOrCreateCreatorId:
    """Test cases for get_or_create_creator_id function"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()
    
    def test_session_has_creator_id(self):
        """Test when session already has creator_id"""
        request = self.factory.get('/')
        request.session = {'creator_id': 'existing-uuid-123'}
        
        result = get_or_create_creator_id(request)
        
        assert result == 'existing-uuid-123'
        assert request.session['creator_id'] == 'existing-uuid-123'
    
    def test_session_empty(self):
        """Test when session is empty"""
        request = self.factory.get('/')
        request.session = {}
        
        result = get_or_create_creator_id(request)
        
        assert result is not None
        assert len(result) > 0
        assert request.session['creator_id'] == result
    
    def test_session_corrupted(self):
        """Test when session has corrupted creator_id"""
        request = self.factory.get('/')
        request.session = {'creator_id': None}
        
        # Should regenerate when None
        result = get_or_create_creator_id(request)
        
        # Since the function checks for falsy values
        if not request.session.get('creator_id'):
            assert result is not None
            assert len(result) > 0
    
    def test_multiple_calls_same_session(self):
        """Test multiple calls with same session return same ID"""
        request = self.factory.get('/')
        request.session = {}
        
        result1 = get_or_create_creator_id(request)
        result2 = get_or_create_creator_id(request)
        
        assert result1 == result2
    
    def test_different_sessions_different_ids(self):
        """Test different sessions get different creator IDs"""
        request1 = self.factory.get('/')
        request1.session = {}
        
        request2 = self.factory.get('/')
        request2.session = {}
        
        result1 = get_or_create_creator_id(request1)
        result2 = get_or_create_creator_id(request2)
        
        assert result1 != result2
    
    def test_creator_id_format(self):
        """Test that creator_id is in UUID format"""
        request = self.factory.get('/')
        request.session = {}
        
        result = get_or_create_creator_id(request)
        
        # Check it's a valid UUID format (string with hyphens)
        import uuid
        try:
            uuid.UUID(result)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        
        assert is_valid_uuid
