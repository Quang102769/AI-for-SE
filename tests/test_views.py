"""
Unit tests for views.py helper functions
Tests for get_or_create_creator_id and other view helpers
"""
import pytest
from unittest.mock import Mock
from django.test import RequestFactory
import uuid

from meetings.views import get_or_create_creator_id


# =============================================================================
# get_or_create_creator_id Tests
# =============================================================================

class TestGetOrCreateCreatorId:
    """Tests for get_or_create_creator_id() helper function"""
    
    def test_first_request_no_session_creator_id(self):
        """Test that UUID is generated and stored in session on first request"""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {}
        
        creator_id = get_or_create_creator_id(request)
        
        # Should return a valid UUID string
        assert creator_id is not None
        assert isinstance(creator_id, str)
        # Validate it's a valid UUID
        try:
            uuid.UUID(creator_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid
        
        # Should be stored in session
        assert 'creator_id' in request.session
        assert request.session['creator_id'] == creator_id
    
    def test_subsequent_request_has_session_creator_id(self):
        """Test that existing UUID is returned on subsequent requests"""
        factory = RequestFactory()
        request = factory.get('/')
        existing_uuid = str(uuid.uuid4())
        request.session = {'creator_id': existing_uuid}
        
        creator_id = get_or_create_creator_id(request)
        
        # Should return existing UUID
        assert creator_id == existing_uuid
        assert request.session['creator_id'] == existing_uuid
    
    def test_multiple_calls_return_same_id(self):
        """Test that multiple calls with same session return same ID"""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {}
        
        creator_id_1 = get_or_create_creator_id(request)
        creator_id_2 = get_or_create_creator_id(request)
        creator_id_3 = get_or_create_creator_id(request)
        
        assert creator_id_1 == creator_id_2
        assert creator_id_2 == creator_id_3
