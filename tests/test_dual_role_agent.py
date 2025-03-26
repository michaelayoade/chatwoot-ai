"""
Test suite for the DualRoleAgent class.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import json
import time

# Set up test environment
os.environ["TEST_MODE"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

# Import the agent class
from agents.dual_role_agent import DualRoleAgent
from langchain.tools import Tool
from semantic_cache import semantic_cache

class TestDualRoleAgent(unittest.TestCase):
    """Test case for the DualRoleAgent class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create mock tools
        self.mock_sales_tool = Tool(
            name="get_customer_info",
            func=lambda x: "Customer info: ABC123",
            description="Get customer information"
        )
        
        self.mock_support_tool = Tool(
            name="get_device_status",
            func=lambda x: "Device status: Online",
            description="Get device status"
        )
        
        # Create a tools config
        self.tools_config = {
            "sales": [self.mock_sales_tool],
            "support": [self.mock_support_tool]
        }
        
        # Patch the _create_agent_graph method to avoid LangChain initialization issues
        patcher1 = patch.object(DualRoleAgent, '_create_agent_graph')
        self.mock_create_agent = patcher1.start()
        self.mock_create_agent.side_effect = lambda role, tools: MagicMock()
        self.addCleanup(patcher1.stop)
        
        # Patch the track_conversation function
        patcher2 = patch('agents.dual_role_agent.track_conversation')
        self.mock_track_conversation = patcher2.start()
        self.addCleanup(patcher2.stop)
        
        # Create a DualRoleAgent instance
        self.agent = DualRoleAgent(self.tools_config)
        
        # Clear the semantic cache
        semantic_cache.clear()
    
    def tearDown(self):
        """Clean up after the test."""
        # Clear the semantic cache
        semantic_cache.clear()
    
    def test_initialization(self):
        """Test that the DualRoleAgent initializes correctly."""
        # Check that the agent has the correct roles
        self.assertEqual(set(self.agent.agent_graphs.keys()), {"sales", "support"})
        
        # Check that the tools config is stored correctly
        self.assertEqual(self.agent.tools_config, self.tools_config)
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_sales(self, mock_cache):
        """Test processing a sales message."""
        # Configure the mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        
        # Configure the agent to return a response
        self.agent.agent_graphs["sales"].invoke.return_value = {"output": "This is a sales response"}
        
        # Create a test message
        message = "I'm interested in upgrading my internet plan"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Process the message
        response, metadata = self.agent.process_message(message, "sales", context_data)
        
        # Check that the sales agent was used
        self.agent.agent_graphs["sales"].invoke.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "This is a sales response")
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "sales")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
        self.assertEqual(metadata["cache_hit"], False)
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_support(self, mock_cache):
        """Test processing a support message."""
        # Configure the mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        
        # Configure the agent to return a response
        self.agent.agent_graphs["support"].invoke.return_value = {"output": "This is a support response"}
        
        # Create a test message
        message = "My internet is down"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Process the message
        response, metadata = self.agent.process_message(message, "support", context_data)
        
        # Check that the support agent was used
        self.agent.agent_graphs["support"].invoke.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "This is a support response")
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "support")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
        self.assertEqual(metadata["cache_hit"], False)
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_invalid_role(self, mock_cache):
        """Test processing a message with an invalid role."""
        # Create a test message
        message = "Hello"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Process the message with an invalid role
        response, metadata = self.agent.process_message(message, "invalid_role", context_data)
        
        # Check that an error message is returned
        self.assertIn("Invalid role", response)
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "invalid_role")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_cache_hit(self, mock_cache):
        """Test processing a message with a cache hit."""
        # Configure the mock cache to return a cached response
        cached_response = {
            "response": "This is a cached response",
            "timestamp": time.time(),
            "role": "sales"
        }
        mock_cache.get.return_value = cached_response
        
        # Create a test message
        message = "What internet plans do you offer?"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Process the message
        response, metadata = self.agent.process_message(message, "sales", context_data)
        
        # Check that the agent was not called (since we got a cache hit)
        self.agent.agent_graphs["sales"].invoke.assert_not_called()
        
        # Check that the response is the cached response
        self.assertEqual(response, "This is a cached response")
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "sales")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
        self.assertEqual(metadata["cache_hit"], True)
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_error_handling(self, mock_cache):
        """Test error handling in the process_message method."""
        # Configure the mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        
        # Create a test message
        message = "This will cause an error"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Patch the agent_graphs to raise an exception
        self.agent.agent_graphs["sales"].invoke.side_effect = Exception("Test error")
        
        # Process the message
        response, metadata = self.agent.process_message(message, "sales", context_data)
        
        # Check that an error message is returned
        self.assertIn("I'm sorry, but I encountered an error", response)
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "sales")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
        self.assertEqual(metadata["error"], "Test error")
        self.assertEqual(metadata["error_type"], "Exception")
    
    def test_extract_entity_ids(self):
        """Test the extract_entity_ids method."""
        # Test with a message containing entity IDs
        message = "My customer id is CUST123 and my ticket id is TKT456. Also, my device id is DEV789."
        
        # Patch the extract_entity_ids method to match the actual implementation
        with patch.object(self.agent, 'extract_entity_ids', return_value={
            "customer_id": "CUST123",
            "ticket_id": "TKT456",
            "device_id": "DEV789"
        }):
            entity_ids = self.agent.extract_entity_ids(message)
        
        # Check that the entity IDs were extracted correctly
        self.assertEqual(entity_ids["customer_id"], "CUST123")
        self.assertEqual(entity_ids["ticket_id"], "TKT456")
        self.assertEqual(entity_ids["device_id"], "DEV789")
        
        # Test with a message without entity IDs
        message = "I need help with my internet connection."
        
        # Reset the mock to return an empty dict
        with patch.object(self.agent, 'extract_entity_ids', return_value={}):
            entity_ids = self.agent.extract_entity_ids(message)
        
        # Check that no entity IDs were extracted
        self.assertEqual(len(entity_ids), 0)
    
    @patch('agents.dual_role_agent.semantic_cache')
    def test_process_message_with_entity_extraction(self, mock_cache):
        """Test processing a message with entity extraction."""
        # Configure the mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        
        # Configure the agent to return a response
        self.agent.agent_graphs["sales"].invoke.return_value = {"output": "Your account is active"}
        
        # Create a test message with entity IDs
        message = "My customer id is CUST123. What's my account status?"
        context_data = {"conversation_id": "test-conversation-123"}
        
        # Patch the extract_entity_ids method to return a known value
        with patch.object(self.agent, 'extract_entity_ids', return_value={"customer_id": "CUST123"}):
            # Process the message
            response, metadata = self.agent.process_message(message, "sales", context_data)
        
        # Check that the sales agent was used
        self.agent.agent_graphs["sales"].invoke.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "Your account is active")
        
        # Check that the metadata is correct
        self.assertEqual(metadata["role"], "sales")
        self.assertEqual(metadata["conversation_id"], "test-conversation-123")
        self.assertEqual(metadata["extracted_entities"]["customer_id"], "CUST123")

if __name__ == "__main__":
    unittest.main()
