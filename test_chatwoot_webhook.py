"""
Test script for Chatwoot webhook and API reply functionality.
This script simulates a Chatwoot webhook event and tests the response.
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

def test_webhook_processing():
    """Test the webhook processing functionality"""
    print("Testing webhook processing...")
    
    # Create a context manager
    context_manager = ConversationContextManager(storage_path="./data/contexts")
    
    # Create a Chatwoot handler
    chatwoot_handler = ChatwootHandler(
        api_key="test_key",
        account_id="1",
        base_url="https://chatwoot.example.com",
        context_manager=context_manager
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
    
    # Process the webhook
    result = chatwoot_handler.process_webhook(webhook_data)
    
    # Check the result
    print(f"Webhook processing result: {json.dumps(result, indent=2)}")
    
    if result.get("status") == "success":
        print("✅ Webhook processing test passed")
    else:
        print("❌ Webhook processing test failed")
    
    return result

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

def simulate_webhook_request():
    """Simulate a webhook request to the local server"""
    print("\nSimulating webhook request to local server...")
    
    # Check if the server is running
    try:
        response = requests.get("http://localhost:5000/")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the server with 'python app.py'")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server with 'python app.py'")
        return None
    
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
    
    # Send the webhook request
    try:
        response = requests.post(
            "http://localhost:5000/webhook/chatwoot",
            json=webhook_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Check the response
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("status") == "success":
            print("✅ Webhook request simulation passed")
        else:
            print("❌ Webhook request simulation failed")
        
        return response.json()
    except Exception as e:
        print(f"❌ Error simulating webhook request: {str(e)}")
        return None

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("./data/contexts", exist_ok=True)
    
    # Run the tests
    test_webhook_processing()
    test_send_message()
    
    # Simulate a webhook request (only if server is running)
    simulate_webhook_request()
