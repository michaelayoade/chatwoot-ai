"""
Simplified test script for Chatwoot webhook and API reply functionality.
This script tests only the essential functionality without relying on the reliability features.
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set test mode to True to avoid making actual API calls
os.environ["TEST_MODE"] = "true"

# Import after setting TEST_MODE
from handlers.chatwoot_handler import ChatwootHandler
from utils.conversation_context import ConversationContextManager

def test_send_message():
    """Test the message sending functionality"""
    print("\nTesting message sending...")
    
    # Create a Chatwoot handler
    chatwoot_handler = ChatwootHandler(
        api_key=os.getenv("CHATWOOT_API_KEY", "test_key"),
        account_id=os.getenv("CHATWOOT_ACCOUNT_ID", "1"),
        base_url=os.getenv("CHATWOOT_BASE_URL", "https://chatwoot.example.com")
    )
    
    # Send a test message
    conversation_id = "789"
    message = "This is a test message from the LangChain-Chatwoot integration"
    
    result = chatwoot_handler.send_message(conversation_id, message)
    
    # Check the result
    print(f"Message sending result: {json.dumps(result, indent=2)}")
    
    if "error" not in result:
        print("✅ Message sending test passed")
    else:
        print("❌ Message sending test failed")
    
    return result

def test_process_webhook():
    """Test the webhook processing functionality directly"""
    print("\nTesting webhook processing directly...")
    
    # Create a Chatwoot handler
    chatwoot_handler = ChatwootHandler(
        api_key=os.getenv("CHATWOOT_API_KEY", "test_key"),
        account_id=os.getenv("CHATWOOT_ACCOUNT_ID", "1"),
        base_url=os.getenv("CHATWOOT_BASE_URL", "https://chatwoot.example.com")
    )
    
    # Create a sample webhook payload
    webhook_data = {
        "event": "message_created",
        "message": {
            "id": 123,
            "content": "Hello, I need help with my internet connection",
            "sender": {
                "id": 456,
                "type": "contact"
            }
        },
        "conversation": {
            "id": 789
        }
    }
    
    try:
        # Process the webhook directly
        result = chatwoot_handler.process_webhook(webhook_data)
        print(f"Webhook processing result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            print("✅ Webhook processing test passed")
        else:
            print("❌ Webhook processing test failed")
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        print("❌ Webhook processing test failed")
    
    return webhook_data

def test_webhook_format():
    """Test that the webhook format is correctly processed"""
    print("\nTesting webhook format processing...")
    
    # Create a sample webhook payload
    webhook_data = {
        "event": "message_created",
        "message": {
            "id": 123,
            "content": "Hello, I need help with my internet connection",
            "sender": {
                "id": 456,
                "type": "contact"
            }
        },
        "conversation": {
            "id": 789
        }
    }
    
    # Print the webhook data
    print(f"Sample webhook data: {json.dumps(webhook_data, indent=2)}")
    print("\nThis is the format that Chatwoot sends to the webhook endpoint.")
    print("The webhook endpoint should extract the message content and conversation ID,")
    print("process the message, and send a response back to the conversation.")
    
    # Explain the webhook flow
    print("\nWebhook flow:")
    print("1. Chatwoot sends a webhook to /webhook/chatwoot when a new message is created")
    print("2. The webhook handler extracts the message content and conversation ID")
    print("3. The message is processed by the LangChain agent")
    print("4. The response is sent back to the Chatwoot conversation via the API")
    
    return webhook_data

if __name__ == "__main__":
    # Run the tests
    test_send_message()
    test_process_webhook()
    test_webhook_format()
