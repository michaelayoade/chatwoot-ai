"""
Test script for the dual-role agent implementation.
This script simulates conversations to test the agent's ability to switch between sales and support roles.
"""

import os
import json
import logging
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test")

# Ensure we're in test mode
os.environ["TEST_MODE"] = "True"

from conversation_context import ConversationContextManager
from langchain_integration import process_message, chatwoot_handler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_conversation(conversation_id, messages, context_manager):
    """
    Simulate a conversation with the dual-role agent.
    
    Args:
        conversation_id: The ID of the simulated conversation
        messages: List of messages to process
        context_manager: The conversation context manager
    """
    print(f"\n=== Starting conversation {conversation_id} ===\n")
    
    for i, message in enumerate(messages):
        print(f"\nUser: {message}")
        
        # Process the message
        response = process_message(message, conversation_id, context_manager)
        
        # Print the response
        print(f"Agent: {response}")
        
        # Print the current role
        current_role = context_manager.get_current_role(conversation_id)
        print(f"Current role: {current_role}")
        
        # Print a separator
        print("\n" + "-" * 50)
    
    # Print the final conversation context
    context = context_manager.get_conversation_summary(conversation_id)
    print("\nFinal conversation context:")
    print(json.dumps(context, indent=2))
    
    print(f"\n=== End of conversation {conversation_id} ===\n")

def main():
    """Main test function"""
    # Initialize the conversation context manager
    context_manager = ConversationContextManager()
    
    # Set the chatwoot handler's context manager
    chatwoot_handler.context_manager = context_manager
    
    # Test case 1: Sales conversation
    sales_conversation = [
        "Hi, I'm interested in getting internet service for my new home.",
        "What plans do you offer for residential customers?",
        "Do you have any promotions for new customers?",
        "What's the installation process like?",
        "I think I'm ready to sign up for the 100 Mbps plan."
    ]
    
    # Test case 2: Support conversation
    support_conversation = [
        "My internet is not working properly.",
        "I've already tried restarting my router.",
        "My customer ID is CUS-12345.",
        "When will the technician arrive?",
        "Thank you for your help."
    ]
    
    # Test case 3: Mixed conversation (starting with sales, switching to support)
    mixed_conversation = [
        "Hi, I'm looking for information about your fiber plans.",
        "What's the fastest plan you offer?",
        "Actually, I'm already a customer and my internet is down.",
        "My customer ID is CUS-67890.",
        "I've tried restarting my router but it's still not working."
    ]
    
    # Run the test cases
    simulate_conversation("sales-test", sales_conversation, context_manager)
    simulate_conversation("support-test", support_conversation, context_manager)
    simulate_conversation("mixed-test", mixed_conversation, context_manager)

if __name__ == "__main__":
    main()
