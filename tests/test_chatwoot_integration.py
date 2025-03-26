"""
Integration tests for Chatwoot handler with mocked API.
"""
import unittest
from unittest.mock import MagicMock, patch, call
import json
import os
import sys
from typing import Dict, Any, List

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules for testing
from handlers.chatwoot_handler import ChatwootHandler

class MockResponse:
    """Mock response object for requests library."""
    
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
        
    def json(self):
        return self.json_data

class TestChatwootIntegration(unittest.TestCase):
    """Integration tests for Chatwoot handler with mocked API."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'CHATWOOT_API_KEY': 'test-api-key',
            'CHATWOOT_BASE_URL': 'https://test-chatwoot.example.com',
            'CHATWOOT_ACCOUNT_ID': '123',
            'TESTING': 'True'
        })
        self.env_patcher.start()
        
        # Create the handler with mocked dependencies
        self.context_manager = MagicMock()
        self.handler = ChatwootHandler(
            api_key='test-api-key',
            account_id='123',
            base_url='https://test-chatwoot.example.com',
            context_manager=self.context_manager
        )
        
        # Mock the requests module
        self.requests_patcher = patch('handlers.chatwoot_handler.requests')
        self.mock_requests = self.requests_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.requests_patcher.stop()
    
    def test_send_message(self):
        """Test sending a message to Chatwoot API."""
        # Set up mock response
        self.mock_requests.post.return_value = MockResponse({"id": 54321}, 200)
        
        # Call the send_message method
        result = self.handler.send_message(
            conversation_id=67890,
            message="Test response"
        )
        
        # In test mode, the handler returns a predefined response
        expected_test_response = {"status": "success", "message": "Message sent (test mode)"}
        self.assertEqual(result, expected_test_response)
        
        # Verify the API was not called in test mode
        self.mock_requests.post.assert_not_called()
        
        # Test with test_mode disabled
        # Temporarily set test_mode to False
        self.handler.test_mode = False
        
        # Call the method again
        result = self.handler.send_message(
            conversation_id=67890,
            message="Test response"
        )
        
        # Now we should get the actual API response
        self.assertEqual(result, {"id": 54321})
        
        # Verify API call was made
        expected_url = f"https://test-chatwoot.example.com/api/v1/accounts/123/conversations/67890/messages"
        expected_headers = {
            "api_access_token": "test-api-key",
            "Content-Type": "application/json"
        }
        expected_payload = {
            "content": "Test response",
            "message_type": "outgoing"
        }
        
        self.mock_requests.post.assert_called_once_with(
            expected_url, 
            headers=expected_headers, 
            json=expected_payload,
            timeout=10
        )

if __name__ == "__main__":
    unittest.main()
