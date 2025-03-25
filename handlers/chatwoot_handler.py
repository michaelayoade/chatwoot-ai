"""
Chatwoot integration handler for processing webhooks and sending messages.
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional

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
    
    def process_webhook(self, webhook_data: Dict) -> Dict:
        """Process incoming webhook data from Chatwoot"""
        if not webhook_data:
            return {"error": "No webhook data provided"}
        
        try:
            # Extract relevant information from the webhook
            event_type = webhook_data.get("event")
            if event_type != "message_created":
                return {"status": "ignored", "reason": f"Event type {event_type} not handled"}
            
            message_data = webhook_data.get("message", {})
            conversation_id = str(webhook_data.get("conversation", {}).get("id"))
            
            # Check if the message is from a user (not from the agent/bot)
            if message_data.get("sender", {}).get("type") != "contact":
                return {"status": "ignored", "reason": "Message not from contact"}
            
            # Extract the message content
            message_content = message_data.get("content")
            if not message_content:
                return {"status": "ignored", "reason": "Empty message content"}
            
            # Get conversation history
            history = self.get_conversation_history(conversation_id)
            
            # Update the conversation context
            if self.context_manager:
                self.context_manager.update_context(conversation_id, message_content, history)
            
            # Process the message using the agent
            from langchain_integration import process_message
            response = process_message(message_content, conversation_id, self.context_manager)
            
            # Send the response back to the conversation
            self.send_message(conversation_id, response)
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message": message_content,
                "response": response
            }
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return {"error": f"Failed to process webhook: {str(e)}"}
    
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
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return {"error": f"Failed to send message: {str(e)}"}
    
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
        from langchain_integration import process_message
        
        # Tag the conversation as sales
        self.tag_conversation(conversation_id, "sales")
        
        # Process the message with the sales role
        if self.context_manager:
            self.context_manager.set_role(conversation_id, "sales")
        
        response = process_message(query, conversation_id, self.context_manager)
        return response
    
    def handle_support_query(self, conversation_id: str, query: str, customer_id: str = None) -> str:
        """Handle a support-related query using the Splynx and UNMS tools"""
        from langchain_integration import process_message
        
        # Tag the conversation as support
        self.tag_conversation(conversation_id, "support")
        
        # Process the message with the support role
        if self.context_manager:
            self.context_manager.set_role(conversation_id, "support")
        
        response = process_message(query, conversation_id, self.context_manager)
        return response
