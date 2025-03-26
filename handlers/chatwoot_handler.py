"""
Chatwoot integration handler for processing webhooks and sending messages.
"""
import os
import json
import requests
import time
from typing import Dict, List, Any, Optional
import traceback
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("CHATWOOT_API_KEY") in [None, "", "your_chatwoot_api_key"]
)

class ChatwootHandler:
    """Handler for Chatwoot webhooks and message sending."""
    
    def __init__(self, api_key: str, account_id: str, base_url: str, context_manager=None):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url
        self.test_mode = TEST_MODE or os.getenv("TEST_MODE", "").lower() == "true"
        self.context_manager = context_manager
        self.headers = {
            "api_access_token": self.api_key,
            "Content-Type": "application/json"
        }
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook from Chatwoot.
        
        Args:
            webhook_data: The webhook data from Chatwoot
            
        Returns:
            Dictionary with processing result
        """
        try:
            print(f"Received Chatwoot webhook: {json.dumps(webhook_data)}...")
            
            # Check if this is a message event
            event = webhook_data.get("event")
            if event != "message_created":
                return {
                    "status": "ignored",
                    "reason": f"Event type '{event}' is not supported"
                }
            
            # Extract message data
            message_data = webhook_data.get("message", {})
            conversation_data = webhook_data.get("conversation", {})
            
            # Check if this is a message from a contact (not from the bot)
            sender = message_data.get("sender", {})
            if sender.get("type") != "contact":
                return {
                    "status": "ignored",
                    "reason": "Message is not from a contact"
                }
            
            # Extract message content and conversation ID
            message_content = message_data.get("content", "")
            conversation_id = str(conversation_data.get("id", ""))
            
            # Get conversation history
            try:
                history = self.get_conversation_history(conversation_id)
                print(f"[TEST MODE] Getting history for conversation {conversation_id}")
            except Exception as e:
                print(f"Error getting conversation history: {str(e)}")
                history = []
            
            # Process the message
            try:
                # Import here to avoid circular imports
                from langchain_integration import process_message
                response = process_message(
                    message_content, 
                    conversation_id,
                    self.context_manager
                )
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                response = "I'm sorry, but I encountered an error while processing your request. Please try again or contact customer support for assistance."
            
            # Send the response back to Chatwoot
            try:
                reply_result = self.send_message(conversation_id, response)
                print(f"Processed webhook for conversation {conversation_id}. Message: '{message_content}', Response: '{response}'")
            except Exception as e:
                print(f"Error sending message to Chatwoot: {str(e)}")
                reply_result = {
                    "status": "error",
                    "message": str(e)
                }
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message": message_content,
                "response": response,
                "reply_result": reply_result
            }
            
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def send_message(self, conversation_id: str, message: str) -> Dict:
        """Send a message to a Chatwoot conversation"""
        if self.test_mode:
            print(f"[TEST MODE] Sending message to conversation {conversation_id}: {message}")
            return {"status": "success", "message": "Message sent (test mode)"}
        
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        payload = {
            "content": message,
            "message_type": "outgoing"
        }
        
        # Add retry logic for API calls
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Sending message to Chatwoot (attempt {attempt+1}/{max_retries}): {url}")
                response = requests.post(url, headers=self.headers, json=payload, timeout=10)
                
                # Log the response status
                print(f"Chatwoot API response status: {response.status_code}")
                
                # Check if the request was successful
                if response.status_code == 200 or response.status_code == 201:
                    response_data = response.json()
                    print(f"Successfully sent message to conversation {conversation_id}")
                    return response_data
                else:
                    print(f"Error from Chatwoot API: Status {response.status_code}, Response: {response.text[:200]}")
                    
                    # If we've reached the max retries, raise an exception
                    if attempt == max_retries - 1:
                        response.raise_for_status()
                    
                    # Otherwise, wait and retry
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            except requests.exceptions.Timeout:
                print(f"Timeout connecting to Chatwoot API (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {"error": "Timeout connecting to Chatwoot API"}
                time.sleep(retry_delay)
                retry_delay *= 2
            except requests.exceptions.ConnectionError:
                print(f"Connection error to Chatwoot API (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {"error": "Connection error to Chatwoot API"}
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                if attempt == max_retries - 1:
                    return {"error": f"Failed to send message: {str(e)}"}
                time.sleep(retry_delay)
                retry_delay *= 2
        
        # If we get here, all retries failed
        return {"error": "Failed to send message after multiple attempts"}
    
    def tag_conversation(self, conversation_id: str, tag_name: str) -> Dict:
        """Tag a conversation with a specific label"""
        if self.test_mode:
            print(f"[TEST MODE] Tagging conversation {conversation_id} with: {tag_name}")
            return {"status": "success", "message": "Conversation tagged (test mode)"}
        
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/labels"
        payload = {
            "labels": [tag_name]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error tagging conversation: {str(e)}")
            return {"error": f"Failed to tag conversation: {str(e)}"}
    
    def get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[Dict]:
        """Get the message history for a conversation"""
        if self.test_mode:
            print(f"[TEST MODE] Getting history for conversation {conversation_id}")
            # Return mock conversation history
            return [
                {
                    "id": 1,
                    "content": "Hello, I need help with my internet connection.",
                    "message_type": "incoming",
                    "created_at": "2025-03-24T14:30:00Z"
                },
                {
                    "id": 2,
                    "content": "Hi there! I'd be happy to help. Could you please provide your customer ID?",
                    "message_type": "outgoing",
                    "created_at": "2025-03-24T14:31:00Z"
                },
                {
                    "id": 3,
                    "content": "My customer ID is CUS-12345.",
                    "message_type": "incoming",
                    "created_at": "2025-03-24T14:32:00Z"
                }
            ]
        
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages?limit={limit}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting conversation history: {str(e)}")
            return []
    
    def update_conversation_status(self, conversation_id: str, status: str) -> Dict:
        """Update the status of a conversation (open, resolved, pending)"""
        if status not in ["open", "resolved", "pending"]:
            return {"error": "Invalid status. Must be one of: open, resolved, pending"}
        
        if self.test_mode:
            print(f"[TEST MODE] Updating conversation {conversation_id} status to: {status}")
            return {"status": "success", "message": f"Conversation status updated to {status} (test mode)"}
        
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/status"
        payload = {
            "status": status
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating conversation status: {str(e)}")
            return {"error": f"Failed to update conversation status: {str(e)}"}
    
    def assign_conversation(self, conversation_id: str, assignee_id: int) -> Dict:
        """Assign a conversation to a specific agent"""
        if self.test_mode:
            print(f"[TEST MODE] Assigning conversation {conversation_id} to agent {assignee_id}")
            return {"status": "success", "message": f"Conversation assigned to agent {assignee_id} (test mode)"}
        
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/assignments"
        payload = {
            "assignee_id": assignee_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error assigning conversation: {str(e)}")
            return {"error": f"Failed to assign conversation: {str(e)}"}
    
    def handle_sales_query(self, conversation_id: str, query: str, customer_id: str = None) -> str:
        """Handle a sales-related query using the ERPNext tool"""
        # Import here to avoid circular imports
        from langchain_integration import process_message
        
        # Tag the conversation as sales
        self.tag_conversation(conversation_id, "sales")
        
        # Process the message with the sales role
        if self.context_manager:
            self.context_manager.set_role(conversation_id, "sales")
        
        response = process_message(query, conversation_id, self.context_manager)
        
        # Extract just the response text if it's a tuple (response, metadata)
        if isinstance(response, tuple) and len(response) == 2:
            return response[0]
        return response

    def handle_support_query(self, conversation_id: str, query: str, customer_id: str = None) -> str:
        """Handle a support-related query using the Splynx and UNMS tools"""
        # Import here to avoid circular imports
        from langchain_integration import process_message
        
        # Tag the conversation as support
        self.tag_conversation(conversation_id, "support")
        
        # Process the message with the support role
        if self.context_manager:
            self.context_manager.set_role(conversation_id, "support")
        
        response = process_message(query, conversation_id, self.context_manager)
        
        # Extract just the response text if it's a tuple (response, metadata)
        if isinstance(response, tuple) and len(response) == 2:
            return response[0]
        return response
