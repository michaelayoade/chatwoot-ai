"""
Tests for the prometheus_metrics.py module.
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import time
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from prometheus_metrics import track_conversation, track_request

class TestPrometheusMetrics(unittest.TestCase):
    """Test the prometheus_metrics module."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock logger
        self.mock_logger = MagicMock()
        self.logger_patch = patch('prometheus_metrics.logger', self.mock_logger)
        self.logger_patch.start()
    
    def tearDown(self):
        """Tear down the test environment."""
        # Stop the patches
        self.logger_patch.stop()
    
    def test_track_conversation_success(self):
        """Test the track_conversation decorator with a successful function call."""
        # Create a test function
        @track_conversation
        def test_function(message, conversation_id):
            return f"Processed: {message}"
        
        # Call the function
        result = test_function("Hello", "conv-123")
        
        # Check the result
        self.assertEqual(result, "Processed: Hello")
        
        # Check that the logger was called with the right arguments
        self.mock_logger.info.assert_called_once()
        args, kwargs = self.mock_logger.info.call_args
        self.assertEqual(args[0], "conversation_processed")
        self.assertEqual(kwargs["conversation_id"], "conv-123")
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "success")
    
    def test_track_conversation_failure(self):
        """Test the track_conversation decorator with a failing function call."""
        # Create a test function that raises an exception
        @track_conversation
        def test_function(message, conversation_id):
            raise ValueError("Test error")
        
        # Call the function and expect an exception
        with self.assertRaises(ValueError):
            test_function("Hello", "conv-123")
        
        # Check that the logger was called with the right arguments
        self.mock_logger.error.assert_called_once()
        args, kwargs = self.mock_logger.error.call_args
        self.assertEqual(args[0], "conversation_failed")
        self.assertEqual(kwargs["conversation_id"], "conv-123")
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "error")
        self.assertEqual(kwargs["error"], "Test error")
    
    def test_track_request_success(self):
        """Test the track_request decorator with a successful function call."""
        # Create a test function
        @track_request(endpoint_name="test_endpoint")
        def test_function():
            return "Success"
        
        # Call the function
        result = test_function()
        
        # Check the result
        self.assertEqual(result, "Success")
        
        # Check that the logger was called with the right arguments
        self.mock_logger.info.assert_called_once()
        args, kwargs = self.mock_logger.info.call_args
        self.assertEqual(args[0], "api_request")
        self.assertEqual(kwargs["endpoint"], "test_endpoint")
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "success")
    
    def test_track_request_failure(self):
        """Test the track_request decorator with a failing function call."""
        # Create a test function that raises an exception
        @track_request(endpoint_name="test_endpoint")
        def test_function():
            raise ValueError("Test error")
        
        # Call the function and expect an exception
        with self.assertRaises(ValueError):
            test_function()
        
        # Check that the logger was called with the right arguments
        self.mock_logger.error.assert_called_once()
        args, kwargs = self.mock_logger.error.call_args
        self.assertEqual(args[0], "api_request_failed")
        self.assertEqual(kwargs["endpoint"], "test_endpoint")
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "error")
        self.assertEqual(kwargs["error"], "Test error")
    
    def test_track_request_no_endpoint_name(self):
        """Test the track_request decorator without an endpoint name."""
        # Create a test function
        @track_request
        def test_function():
            return "Success"
        
        # Call the function
        result = test_function()
        
        # Check the result
        self.assertEqual(result, "Success")
        
        # Check that the logger was called with the right arguments
        self.mock_logger.info.assert_called_once()
        args, kwargs = self.mock_logger.info.call_args
        self.assertEqual(args[0], "api_request")
        self.assertEqual(kwargs["endpoint"], "test_function")  # Should use the function name
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "success")
    
    def test_track_request_with_args(self):
        """Test the track_request decorator with arguments."""
        # Create a test function
        @track_request(endpoint_name="test_with_args")
        def test_function(arg1, arg2):
            return f"{arg1} {arg2}"
        
        # Call the function
        result = test_function("Hello", "World")
        
        # Check the result
        self.assertEqual(result, "Hello World")
        
        # Check that the logger was called with the right arguments
        self.mock_logger.info.assert_called_once()
        args, kwargs = self.mock_logger.info.call_args
        self.assertEqual(args[0], "api_request")
        self.assertEqual(kwargs["endpoint"], "test_with_args")
        self.assertIn("duration_seconds", kwargs)
        self.assertEqual(kwargs["status"], "success")

if __name__ == '__main__':
    unittest.main()
