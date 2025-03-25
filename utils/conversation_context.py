"""
Conversation context manager for tracking conversation state and roles.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class ConversationContextManager:
    """
    Manages conversation context, including role detection and entity tracking.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the conversation context manager.
        
        Args:
            storage_path: Optional path to store conversation context data
        """
        self.contexts = {}
        self.storage_path = storage_path
        
        # Create storage directory if it doesn't exist
        if storage_path and not os.path.exists(storage_path):
            os.makedirs(storage_path)
        
        # Load existing contexts if available
        if storage_path and os.path.exists(os.path.join(storage_path, "contexts.json")):
            self._load_contexts()
    
    def _load_contexts(self):
        """Load conversation contexts from storage"""
        try:
            with open(os.path.join(self.storage_path, "contexts.json"), "r") as f:
                self.contexts = json.load(f)
        except Exception as e:
            print(f"Error loading conversation contexts: {str(e)}")
    
    def _save_contexts(self):
        """Save conversation contexts to storage"""
        if not self.storage_path:
            return
        
        try:
            with open(os.path.join(self.storage_path, "contexts.json"), "w") as f:
                json.dump(self.contexts, f)
        except Exception as e:
            print(f"Error saving conversation contexts: {str(e)}")
    
    def get_conversation_context(self, conversation_id: str) -> Dict:
        """
        Get the context for a specific conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context
        """
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = {
                "role": "support",  # Default role
                "entities": {},
                "summary": "",
                "history": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_contexts()
        
        return self.contexts[conversation_id]
    
    def update_context(self, conversation_id: str, message: str, history: List[Dict] = None) -> None:
        """
        Update the context for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            message: The latest message
            history: Optional conversation history
        """
        context = self.get_conversation_context(conversation_id)
        
        # Update history
        if history:
            context["history"] = history
        elif message:
            context["history"].append({
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
        
        # Detect role from message content
        if message:
            self._detect_role(conversation_id, message)
        
        # Update timestamp
        context["last_updated"] = datetime.now().isoformat()
        
        # Save contexts
        self._save_contexts()
    
    def _detect_role(self, conversation_id: str, message: str) -> None:
        """
        Detect the appropriate role based on message content.
        
        Args:
            conversation_id: The ID of the conversation
            message: The message to analyze
        """
        context = self.get_conversation_context(conversation_id)
        
        # Simple keyword-based role detection
        sales_keywords = [
            "buy", "purchase", "order", "price", "cost", "subscription", "plan", 
            "package", "offer", "promotion", "discount", "deal", "upgrade", 
            "interested in", "sign up", "subscribe"
        ]
        
        support_keywords = [
            "help", "issue", "problem", "trouble", "not working", "error", "fix", 
            "broken", "slow", "connection", "speed", "outage", "down", "technical", 
            "support", "assistance", "troubleshoot"
        ]
        
        message_lower = message.lower()
        
        # Count keyword matches
        sales_count = sum(1 for keyword in sales_keywords if keyword in message_lower)
        support_count = sum(1 for keyword in support_keywords if keyword in message_lower)
        
        # Determine role based on keyword counts
        if sales_count > support_count:
            context["role"] = "sales"
        elif support_count > sales_count:
            context["role"] = "support"
        # If counts are equal, keep the existing role
    
    def set_role(self, conversation_id: str, role: str) -> None:
        """
        Manually set the role for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            role: The role to set ("sales" or "support")
        """
        if role not in ["sales", "support"]:
            raise ValueError(f"Invalid role: {role}. Must be one of: sales, support")
        
        context = self.get_conversation_context(conversation_id)
        context["role"] = role
        self._save_contexts()
    
    def get_current_role(self, conversation_id: str) -> str:
        """
        Get the current role for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The current role ("sales" or "support")
        """
        context = self.get_conversation_context(conversation_id)
        return context.get("role", "support")
    
    def update_entities(self, conversation_id: str, entities: Dict[str, str]) -> None:
        """
        Update the entities for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            entities: Dictionary of entity IDs
        """
        context = self.get_conversation_context(conversation_id)
        
        if "entities" not in context:
            context["entities"] = {}
        
        context["entities"].update(entities)
        self._save_contexts()
    
    def get_entities(self, conversation_id: str) -> Dict[str, str]:
        """
        Get the entities for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dictionary of entity IDs
        """
        context = self.get_conversation_context(conversation_id)
        return context.get("entities", {})
    
    def update_summary(self, conversation_id: str, summary: str) -> None:
        """
        Update the summary for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            summary: The conversation summary
        """
        context = self.get_conversation_context(conversation_id)
        context["summary"] = summary
        self._save_contexts()
    
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """
        Get a summary of the conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dictionary containing conversation summary
        """
        context = self.get_conversation_context(conversation_id)
        
        return {
            "role": context.get("role", "support"),
            "entities": context.get("entities", {}),
            "summary": context.get("summary", ""),
            "last_updated": context.get("last_updated", "")
        }
    
    def clear_context(self, conversation_id: str) -> None:
        """
        Clear the context for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            self._save_contexts()
