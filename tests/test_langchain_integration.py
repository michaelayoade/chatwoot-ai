"""
Tests for the langchain_integration.py module.
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from langchain_integration import process_message, extract_entity_ids

class TestLangchainIntegration(unittest.TestCase):
    """Test the langchain_integration module."""

    def setUp(self):
        """Set up the test environment."""
        # Create mock agents
        self.mock_sales_agent = MagicMock()
        self.mock_sales_agent.process_message.return_value = ("Sales response", {"metadata": "sales"})
        
        self.mock_support_agent = MagicMock()
        self.mock_support_agent.process_message.return_value = ("Support response", {"metadata": "support"})
        
        # Create mock context manager
        self.mock_context_manager = MagicMock()
        self.mock_context_manager.get_current_role.return_value = "sales"
        self.mock_context_manager.get_conversation_summary.return_value = {
            "role": "sales",
            "entities": {"customer_id": "123"}
        }
        
        # Set up the patches
        self.sales_agent_patch = patch('langchain_integration.sales_agent', self.mock_sales_agent)
        self.support_agent_patch = patch('langchain_integration.support_agent', self.mock_support_agent)
        
        # Start the patches
        self.sales_agent_patch.start()
        self.support_agent_patch.start()
    
    def tearDown(self):
        """Tear down the test environment."""
        # Stop the patches
        self.sales_agent_patch.stop()
        self.support_agent_patch.stop()
    
    def test_extract_entity_ids(self):
        """Test the extract_entity_ids function."""
        # Test with customer ID
        message = "My customer ID is CID-12345"
        entity_ids = extract_entity_ids(message)
        self.assertEqual(entity_ids.get("customer_id"), "CID-12345")
        
        # Test with order ID
        message = "My order ID is ORD-67890"
        entity_ids = extract_entity_ids(message)
        self.assertEqual(entity_ids.get("order_id"), "ORD-67890")
        
        # Test with multiple entities
        message = "My customer ID is CID-12345 and my order ID is ORD-67890"
        entity_ids = extract_entity_ids(message)
        self.assertEqual(entity_ids.get("customer_id"), "CID-12345")
        self.assertEqual(entity_ids.get("order_id"), "ORD-67890")
        
        # Test with no entities
        message = "I need help with my internet connection"
        entity_ids = extract_entity_ids(message)
        self.assertEqual(entity_ids, {})
    
    @patch('langchain_integration.track_conversation')
    def test_process_message_sales_role(self, mock_track_conversation):
        """Test the process_message function with sales role."""
        # Set up the mock
        mock_track_conversation.return_value = lambda func: func
        
        # Call the function
        response = process_message("I want to buy internet", "conv-123", self.mock_context_manager)
        
        # Check the response
        self.assertEqual(response, "Sales response")
        
        # Check that the sales agent was called with the right arguments
        self.mock_sales_agent.process_message.assert_called_once()
        args, kwargs = self.mock_sales_agent.process_message.call_args
        self.assertEqual(args[0], "I want to buy internet")
        self.assertIsInstance(args[1], dict)
        self.assertEqual(args[1].get("role"), "sales")
        self.assertIsInstance(args[1].get("entities"), dict)
        
        # Check that the support agent was not called
        self.mock_support_agent.process_message.assert_not_called()
    
    @patch('langchain_integration.track_conversation')
    def test_process_message_support_role(self, mock_track_conversation):
        """Test the process_message function with support role."""
        # Set up the mock
        mock_track_conversation.return_value = lambda func: func
        
        # Change the role to support
        self.mock_context_manager.get_current_role.return_value = "support"
        self.mock_context_manager.get_conversation_summary.return_value = {
            "role": "support",
            "entities": {"customer_id": "123"}
        }
        
        # Call the function
        response = process_message("I need help with my internet", "conv-123", self.mock_context_manager)
        
        # Check the response
        self.assertEqual(response, "Support response")
        
        # Check that the support agent was called with the right arguments
        self.mock_support_agent.process_message.assert_called_once()
        args, kwargs = self.mock_support_agent.process_message.call_args
        self.assertEqual(args[0], "I need help with my internet")
        self.assertIsInstance(args[1], dict)
        self.assertEqual(args[1].get("role"), "support")
        self.assertIsInstance(args[1].get("entities"), dict)
        
        # Check that the sales agent was not called
        self.mock_sales_agent.process_message.assert_not_called()
    
    @patch('langchain_integration.track_conversation')
    def test_process_message_no_context_manager(self, mock_track_conversation):
        """Test the process_message function with no context manager."""
        # Set up the mock
        mock_track_conversation.return_value = lambda func: func
        
        # Call the function with no context manager
        response = process_message("I need help", "conv-123", None)
        
        # Check the response
        self.assertEqual(response, "Support response")
        
        # Check that the support agent was called (default role)
        self.mock_support_agent.process_message.assert_called_once()
        
        # Check that the sales agent was not called
        self.mock_sales_agent.process_message.assert_not_called()
    
    @patch('langchain_integration.track_conversation')
    def test_process_message_with_entity_extraction(self, mock_track_conversation):
        """Test the process_message function with entity extraction."""
        # Set up the mock
        mock_track_conversation.return_value = lambda func: func
        
        # Call the function with a message containing entities
        response = process_message("My customer ID is CID-12345", "conv-123", self.mock_context_manager)
        
        # Check the response
        self.assertEqual(response, "Sales response")
        
        # Check that the context manager's update_entities method was called
        self.mock_context_manager.update_entities.assert_called_once()
        args, kwargs = self.mock_context_manager.update_entities.call_args
        self.assertEqual(args[0], "conv-123")
        self.assertIsInstance(args[1], dict)
        self.assertEqual(args[1].get("customer_id"), "CID-12345")
    
    @patch('langchain_integration.track_conversation')
    def test_process_message_error_handling(self, mock_track_conversation):
        """Test the process_message function's error handling."""
        # Set up the mock
        mock_track_conversation.return_value = lambda func: func
        
        # Make the sales agent raise an exception
        self.mock_sales_agent.process_message.side_effect = Exception("Test error")
        
        # Call the function
        response = process_message("I want to buy internet", "conv-123", self.mock_context_manager)
        
        # Check that we got an error response
        self.assertIn("I'm sorry", response)
        self.assertIn("error", response.lower())

if __name__ == '__main__':
    unittest.main()
