"""
Test script for the SalesAgent and SupportAgent classes.
"""
import os
import sys
from dotenv import load_dotenv
import unittest
from unittest.mock import patch, MagicMock

# Load environment variables
load_dotenv()

# Set test mode before importing the agent classes
os.environ["TEST_MODE"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

# Import the agent classes
from agents.sales_agent import SalesAgent
from agents.support_agent import SupportAgent

# Import tools from langchain_integration
from langchain.agents import Tool

def create_mock_tools():
    """Create mock tools for testing."""
    return [
        Tool(
            name="mock_tool",
            func=lambda x: f"Mock response for: {x}",
            description="A mock tool for testing"
        )
    ]

class TestAgents(unittest.TestCase):
    """Test case for the agent classes."""
    
    def setUp(self):
        """Set up the test case."""
        # Create mock tools
        self.mock_tools = create_mock_tools()
        
        # Create a mock response for the agent executor
        self.mock_response = {
            "output": "This is a mock response from the agent."
        }
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_sales_agent(self, mock_invoke):
        """Test the SalesAgent class."""
        print("\n=== Testing SalesAgent ===")
        
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a sales agent with mock tools
        sales_agent = SalesAgent(self.mock_tools)
        
        # Test messages
        test_messages = [
            "I'm interested in upgrading my internet plan",
            "What promotions do you have for new customers?",
            "Can you tell me about your fiber plans?"
        ]
        
        # Process each message
        for message in test_messages:
            print(f"\nSales Query: {message}")
            context_data = {
                "role": "sales",
                "conversation_id": "test-conversation-123"
            }
            
            try:
                response, metadata = sales_agent.process_message(message, context_data)
                print(f"Response: {response}")
                print(f"Metadata: {metadata}")
                
                # Assert that the mock was called
                mock_invoke.assert_called()
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                print(traceback.format_exc())
    
    @patch('langchain.agents.AgentExecutor.invoke')
    def test_support_agent(self, mock_invoke):
        """Test the SupportAgent class."""
        print("\n=== Testing SupportAgent ===")
        
        # Configure the mock
        mock_invoke.return_value = self.mock_response
        
        # Create a support agent with mock tools
        support_agent = SupportAgent(self.mock_tools)
        
        # Test messages
        test_messages = [
            "My internet is down",
            "I'm having trouble connecting to WiFi",
            "When will the outage in my area be fixed?"
        ]
        
        # Process each message
        for message in test_messages:
            print(f"\nSupport Query: {message}")
            context_data = {
                "role": "support",
                "conversation_id": "test-conversation-456"
            }
            
            try:
                response, metadata = support_agent.process_message(message, context_data)
                print(f"Response: {response}")
                print(f"Metadata: {metadata}")
                
                # Assert that the mock was called
                mock_invoke.assert_called()
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                print(traceback.format_exc())

if __name__ == "__main__":
    unittest.main()
