"""
Comprehensive test suite for the SalesAgent and SupportAgent classes.
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

# Import the agent classes
from agents.sales_agent import SalesAgent
from agents.support_agent import SupportAgent
from semantic_cache import semantic_cache

# Import tools from langchain
from langchain.agents import Tool

class MockSemanticCache:
    """Mock implementation of semantic cache for testing."""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value
        return True
    
    def exists(self, key):
        return key in self.cache

def create_mock_tools():
    """Create mock tools for testing."""
    return [
        Tool(
            name="check_service_plans",
            func=lambda x: json.dumps({"fiber": "100Mbps", "cable": "50Mbps"}),
            description="Check available service plans"
        ),
        Tool(
            name="get_promotions",
            func=lambda x: json.dumps({"new_customer": "50% off first 3 months"}),
            description="Get current promotions"
        )
    ]

class TestSalesAgent(unittest.TestCase):
    """Test case for the SalesAgent class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create mock tools
        self.mock_tools = create_mock_tools()
        
        # Create a mock response for the agent executor
        self.mock_response = {
            "output": "This is a mock response from the sales agent."
        }
        
        # Create a patch for the semantic cache
        self.mock_cache = MockSemanticCache()
        self.cache_patcher = patch('agents.sales_agent.semantic_cache', self.mock_cache)
        self.mock_semantic_cache = self.cache_patcher.start()
        
        # Create a context data dictionary
        self.context_data = {
            "role": "sales",
            "conversation_id": "test-conversation-123",
            "customer_id": "cust-456",
            "account_number": "ACC789"
        }
    
    def tearDown(self):
        """Clean up after the test."""
        self.cache_patcher.stop()
    
    def test_initialization(self):
        """Test that the SalesAgent initializes correctly."""
        agent = SalesAgent(self.mock_tools)
        
        # Check that the agent has the correct tools
        self.assertEqual(len(agent.tools), len(self.mock_tools))
        self.assertEqual(agent.tools[0].name, "check_service_plans")
        self.assertEqual(agent.tools[1].name, "get_promotions")
        
        # Check that the agent executor is created
        self.assertIsNotNone(agent.agent_executor)
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_process_message(self, mock_invoke):
        """Test the process_message method."""
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a sales agent
        agent = SalesAgent(self.mock_tools)
        
        # Process a message
        message = "I'm interested in upgrading my internet plan"
        response, metadata = agent.process_message(message, self.context_data)
        
        # Check the response
        self.assertEqual(response, "This is a mock response from the sales agent.")
        self.assertEqual(metadata["role"], "sales")
        self.assertFalse(metadata["cached"])
        self.assertIn("processing_time", metadata)
        
        # Check that the agent executor was called with the correct arguments
        mock_invoke.assert_called_once()
        call_args = mock_invoke.call_args[0][0]
        self.assertEqual(call_args["input"], message)
        self.assertIn("context", call_args)
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_caching(self, mock_invoke):
        """Test that responses are cached and retrieved from cache."""
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a sales agent
        agent = SalesAgent(self.mock_tools)
        
        # Process a message
        message = "What internet plans do you offer?"
        
        # First call should not be cached
        response1, metadata1 = agent.process_message(message, self.context_data)
        self.assertFalse(metadata1["cached"])
        
        # Second call with the same message should be cached
        response2, metadata2 = agent.process_message(message, self.context_data)
        self.assertTrue(metadata2["cached"])
        
        # Check that the agent executor was called only once
        mock_invoke.assert_called_once()
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_extract_entity_ids(self, mock_invoke):
        """Test the extract_entity_ids method."""
        # Configure the mock to return a response
        mock_invoke.return_value = {
            "output": "I found your account information."
        }
        
        # Create a sales agent
        agent = SalesAgent(self.mock_tools)
        
        # Mock the extract_entity_ids method to return the entities
        original_extract_entity_ids = agent.extract_entity_ids
        agent.extract_entity_ids = MagicMock(return_value={
            "customer_id": "CUST123",
            "account_number": "ACC456"
        })
        
        try:
            # Process a message
            message = "Look up my account information"
            response, metadata = agent.process_message(message, self.context_data)
            
            # Check that the entity IDs were extracted
            self.assertIn("entities", metadata)
            entities = metadata["entities"]
            self.assertIn("customer_id", entities)
            self.assertEqual(entities["customer_id"], "CUST123")
            self.assertIn("account_number", entities)
            self.assertEqual(entities["account_number"], "ACC456")
        finally:
            # Restore the original method
            agent.extract_entity_ids = original_extract_entity_ids
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_error_handling(self, mock_invoke):
        """Test error handling in the process_message method."""
        # Configure the mock to raise an exception
        mock_invoke.side_effect = Exception("Test error")
        
        # Create a sales agent
        agent = SalesAgent(self.mock_tools)
        
        # Process a message
        message = "This will cause an error"
        response, metadata = agent.process_message(message, self.context_data)
        
        # Check that a fallback response was returned
        self.assertIn("I'm sorry", response)
        self.assertEqual(metadata["role"], "sales")
        self.assertIn("error", metadata)
        self.assertEqual(metadata["error"], "Test error")

class TestSupportAgent(unittest.TestCase):
    """Test case for the SupportAgent class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create mock tools
        self.mock_tools = [
            Tool(
                name="check_network_status",
                func=lambda x: json.dumps({"status": "operational"}),
                description="Check network status"
            ),
            Tool(
                name="diagnose_connection",
                func=lambda x: json.dumps({"diagnosis": "signal strength low"}),
                description="Diagnose connection issues"
            )
        ]
        
        # Create a mock response for the agent executor
        self.mock_response = {
            "output": "This is a mock response from the support agent."
        }
        
        # Create a patch for the semantic cache
        self.mock_cache = MockSemanticCache()
        self.cache_patcher = patch('agents.support_agent.semantic_cache', self.mock_cache)
        self.mock_semantic_cache = self.cache_patcher.start()
        
        # Create a context data dictionary
        self.context_data = {
            "role": "support",
            "conversation_id": "test-conversation-456",
            "customer_id": "cust-789",
            "device_id": "dev-123"
        }
    
    def tearDown(self):
        """Clean up after the test."""
        self.cache_patcher.stop()
    
    def test_initialization(self):
        """Test that the SupportAgent initializes correctly."""
        agent = SupportAgent(self.mock_tools)
        
        # Check that the agent has the correct tools
        self.assertEqual(len(agent.tools), len(self.mock_tools))
        self.assertEqual(agent.tools[0].name, "check_network_status")
        self.assertEqual(agent.tools[1].name, "diagnose_connection")
        
        # Check that the agent executor is created
        self.assertIsNotNone(agent.agent_executor)
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_process_message(self, mock_invoke):
        """Test the process_message method."""
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a support agent
        agent = SupportAgent(self.mock_tools)
        
        # Process a message
        message = "My internet is down"
        response, metadata = agent.process_message(message, self.context_data)
        
        # Check the response
        self.assertEqual(response, "This is a mock response from the support agent.")
        self.assertEqual(metadata["role"], "support")
        self.assertFalse(metadata["cached"])
        self.assertIn("processing_time", metadata)
        
        # Check that the agent executor was called with the correct arguments
        mock_invoke.assert_called_once()
        call_args = mock_invoke.call_args[0][0]
        self.assertEqual(call_args["input"], message)
        self.assertIn("context", call_args)
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_caching(self, mock_invoke):
        """Test that responses are cached and retrieved from cache."""
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a support agent
        agent = SupportAgent(self.mock_tools)
        
        # Process a message
        message = "Why is my internet slow?"
        
        # First call should not be cached
        response1, metadata1 = agent.process_message(message, self.context_data)
        self.assertFalse(metadata1["cached"])
        
        # Second call with the same message should be cached
        response2, metadata2 = agent.process_message(message, self.context_data)
        self.assertTrue(metadata2["cached"])
        
        # Check that the agent executor was called only once
        mock_invoke.assert_called_once()
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_extract_entity_ids(self, mock_invoke):
        """Test the extract_entity_ids method."""
        # Configure the mock to return a response
        mock_invoke.return_value = {
            "output": "I found your device information."
        }
        
        # Create a support agent
        agent = SupportAgent(self.mock_tools)
        
        # Mock the extract_entity_ids method to return the entities
        original_extract_entity_ids = agent.extract_entity_ids
        agent.extract_entity_ids = MagicMock(return_value={
            "device_id": "DEV789",
            "router_model": "RT-AC68U"
        })
        
        try:
            # Process a message
            message = "Check my router status"
            response, metadata = agent.process_message(message, self.context_data)
            
            # Check that the entity IDs were extracted
            self.assertIn("entities", metadata)
            entities = metadata["entities"]
            self.assertIn("device_id", entities)
            self.assertEqual(entities["device_id"], "DEV789")
            self.assertIn("router_model", entities)
            self.assertEqual(entities["router_model"], "RT-AC68U")
        finally:
            # Restore the original method
            agent.extract_entity_ids = original_extract_entity_ids
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_error_handling(self, mock_invoke):
        """Test error handling in the process_message method."""
        # Configure the mock to raise an exception
        mock_invoke.side_effect = Exception("Test error")
        
        # Create a support agent
        agent = SupportAgent(self.mock_tools)
        
        # Process a message
        message = "This will cause an error"
        response, metadata = agent.process_message(message, self.context_data)
        
        # Check that a fallback response was returned
        self.assertIn("I'm sorry", response)
        self.assertEqual(metadata["role"], "support")
        self.assertIn("error", metadata)
        self.assertEqual(metadata["error"], "Test error")

if __name__ == "__main__":
    unittest.main()
