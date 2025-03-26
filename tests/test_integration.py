"""
Test suite for the integration between the agent classes and Chatwoot.
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

# Import the integration module
import langchain_integration

class MockChatwootHandler:
    """Mock implementation of the Chatwoot handler for testing."""
    
    def __init__(self):
        self.messages = []
        self.conversations = {}
    
    def send_message(self, conversation_id, message, private=False):
        """Mock sending a message to Chatwoot."""
        self.messages.append({
            "conversation_id": conversation_id,
            "message": message,
            "private": private
        })
        return {"id": len(self.messages), "content": message}
    
    def get_conversation(self, conversation_id):
        """Mock getting a conversation from Chatwoot."""
        return self.conversations.get(conversation_id, {
            "id": conversation_id,
            "meta": {"sender": {"name": "Test User"}},
            "messages": []
        })
    
    def get_contact(self, contact_id):
        """Mock getting a contact from Chatwoot."""
        return {
            "id": contact_id,
            "name": "Test Contact",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "custom_attributes": {
                "account_number": "ACC123",
                "customer_id": "CUST456"
            }
        }

class MockContextManager:
    """Mock implementation of the context manager for testing."""
    
    def __init__(self, role="support"):
        self.contexts = {}
        self.default_role = role
    
    def get_current_role(self, conversation_id):
        """Get the current role for a conversation."""
        if conversation_id in self.contexts:
            return self.contexts[conversation_id].get("role", self.default_role)
        return self.default_role
    
    def get_conversation_summary(self, conversation_id):
        """Get the conversation summary."""
        if conversation_id in self.contexts:
            return self.contexts[conversation_id]
        return {"role": self.default_role, "entities": {}}
    
    def update_entities(self, conversation_id, entities):
        """Update the entities for a conversation."""
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = {"role": self.default_role, "entities": {}}
        
        if "entities" not in self.contexts[conversation_id]:
            self.contexts[conversation_id]["entities"] = {}
        
        self.contexts[conversation_id]["entities"].update(entities)

class TestLangchainIntegration(unittest.TestCase):
    """Test case for the Langchain integration."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a mock Chatwoot handler
        self.mock_chatwoot = MockChatwootHandler()
        
        # Create a mock context manager
        self.mock_context_manager = MockContextManager()
        
        # Create patches
        self.chatwoot_patcher = patch.object(langchain_integration, 'chatwoot_handler', self.mock_chatwoot)
        self.mock_chatwoot_handler = self.chatwoot_patcher.start()
        
        # Create mocks for the sales and support agents
        self.mock_sales_agent = MagicMock()
        self.mock_support_agent = MagicMock()
        
        # Configure the mock agents to return test responses
        self.mock_sales_agent.process_message.return_value = (
            "This is a sales response", 
            {"role": "sales", "entities": {}}
        )
        self.mock_support_agent.process_message.return_value = (
            "This is a support response", 
            {"role": "support", "entities": {}}
        )
        
        # Patch the agents in the langchain_integration module
        self.sales_agent_patcher = patch.object(langchain_integration, 'sales_agent', self.mock_sales_agent)
        self.support_agent_patcher = patch.object(langchain_integration, 'support_agent', self.mock_support_agent)
        
        self.mock_sales_agent_obj = self.sales_agent_patcher.start()
        self.mock_support_agent_obj = self.support_agent_patcher.start()
    
    def tearDown(self):
        """Clean up after the test."""
        self.chatwoot_patcher.stop()
        self.sales_agent_patcher.stop()
        self.support_agent_patcher.stop()
    
    @patch.object(langchain_integration, 'extract_entity_ids')
    def test_process_message_sales(self, mock_extract_entity_ids):
        """Test processing a sales message."""
        # Configure the mock to return entities
        mock_extract_entity_ids.return_value = {
            "customer_id": "CUST123",
            "account_number": "ACC456"
        }
        
        # Create a test message
        message = "I'm interested in upgrading my internet plan"
        conversation_id = "test-conversation-456"
        
        # Configure the context manager to indicate a sales role
        context_manager = MockContextManager(role="sales")
        
        # Process the message
        response = langchain_integration.process_message(
            message, 
            conversation_id, 
            context_manager
        )
        
        # Check that the sales agent was used
        self.mock_sales_agent.process_message.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "This is a sales response")
    
    @patch.object(langchain_integration, 'extract_entity_ids')
    def test_process_message_support(self, mock_extract_entity_ids):
        """Test processing a support message."""
        # Configure the mock to return entities
        mock_extract_entity_ids.return_value = {
            "device_id": "DEV789",
            "ticket_number": "TKT456"
        }
        
        # Create a test message
        message = "My internet is down"
        conversation_id = "test-conversation-456"
        
        # Configure the context manager to indicate a support role
        context_manager = MockContextManager(role="support")
        
        # Process the message
        response = langchain_integration.process_message(
            message, 
            conversation_id, 
            context_manager
        )
        
        # Check that the support agent was used
        self.mock_support_agent.process_message.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "This is a support response")
    
    @patch.object(langchain_integration, 'extract_entity_ids')
    def test_process_message_with_entity_extraction(self, mock_extract_entity_ids):
        """Test processing a message with entity extraction."""
        # Configure the mock to return entities
        mock_extract_entity_ids.return_value = {
            "customer_id": "CUST123",
            "account_number": "ACC456"
        }
        
        # Configure the sales agent to return entities in metadata
        self.mock_sales_agent.process_message.return_value = (
            "I found your account", 
            {
                "role": "sales", 
                "entities": {
                    "customer_id": "CUST123", 
                    "account_number": "ACC456"
                }
            }
        )
        
        # Create a test message
        message = "What's my account number?"
        conversation_id = "test-conversation-456"
        
        # Configure the context manager to indicate a sales role
        context_manager = MockContextManager(role="sales")
        
        # Process the message
        response = langchain_integration.process_message(
            message, 
            conversation_id, 
            context_manager
        )
        
        # Check that the sales agent was used
        self.mock_sales_agent.process_message.assert_called_once()
        
        # Check that the response is correct
        self.assertEqual(response, "I found your account")
        
        # Check that the entities were extracted and added to the context
        self.assertEqual(
            context_manager.contexts[conversation_id]["entities"]["customer_id"],
            "CUST123"
        )
        self.assertEqual(
            context_manager.contexts[conversation_id]["entities"]["account_number"],
            "ACC456"
        )
    
    @patch.object(langchain_integration, 'extract_entity_ids')
    def test_process_message_error_handling(self, mock_extract_entity_ids):
        """Test error handling in the process_message function."""
        # Configure the mock to raise an exception
        self.mock_sales_agent.process_message.side_effect = Exception("Test error")
        
        # Create a test message
        message = "This will cause an error"
        conversation_id = "test-conversation-456"
        
        # Configure the context manager to indicate a sales role
        context_manager = MockContextManager(role="sales")
        
        # Process the message
        response = langchain_integration.process_message(
            message, 
            conversation_id, 
            context_manager
        )
        
        # Check that an error message is returned
        self.assertIn("I'm sorry, but I encountered an error", response)

if __name__ == "__main__":
    unittest.main()
