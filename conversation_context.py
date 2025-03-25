import os
import json
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

# Check if we're in test mode
TEST_MODE = os.getenv("TEST_MODE", "True").lower() in ("true", "1", "t")

class ConversationContextManager:
    """
    Manages conversation context to detect whether a conversation is sales or support oriented
    and maintains context over time.
    """
    
    def __init__(self):
        self.contexts = {}  # In-memory storage for test mode
        self.test_mode = TEST_MODE
    
    def detect_role(self, conversation_id: str, message: str, history: List[Dict] = None) -> str:
        """
        Detects whether a conversation is sales or support oriented.
        
        Args:
            conversation_id: The ID of the conversation
            message: The current message content
            history: Previous messages in the conversation
            
        Returns:
            "sales" or "support"
        """
        # Default to previous role if it exists
        if conversation_id in self.contexts:
            previous_role = self.contexts[conversation_id].get("role", "support")
        else:
            previous_role = "support"  # Default to support
        
        # Simple keyword-based detection for demonstration
        sales_keywords = [
            "buy", "purchase", "price", "cost", "plan", "package", "offer", "deal", 
            "subscription", "upgrade", "downgrade", "sign up", "tariff", "promotion",
            "discount", "sale", "interested in", "looking for", "available", "options"
        ]
        
        support_keywords = [
            "help", "issue", "problem", "trouble", "not working", "error", "fix", 
            "broken", "slow", "outage", "down", "connection", "speed", "service",
            "technical", "support", "assistance", "ticket", "complaint"
        ]
        
        # Count keyword matches
        sales_count = sum(1 for keyword in sales_keywords if keyword.lower() in message.lower())
        support_count = sum(1 for keyword in support_keywords if keyword.lower() in message.lower())
        
        # Determine role based on keyword counts
        if sales_count > support_count:
            new_role = "sales"
        elif support_count > sales_count:
            new_role = "support"
        else:
            # If tied or no keywords matched, keep previous role
            new_role = previous_role
            
        # If we have history, use it to refine our detection
        if history and len(history) > 0:
            # Analyze recent history to see if there's a clear trend
            recent_msgs = history[-3:] if len(history) >= 3 else history
            sales_history_count = 0
            support_history_count = 0
            
            for msg in recent_msgs:
                msg_content = msg.get("content", "")
                sales_history_count += sum(1 for keyword in sales_keywords if keyword.lower() in msg_content.lower())
                support_history_count += sum(1 for keyword in support_keywords if keyword.lower() in msg_content.lower())
            
            # If history strongly suggests a different role, override
            if sales_history_count > support_history_count * 2:  # Significantly more sales context
                new_role = "sales"
            elif support_history_count > sales_history_count * 2:  # Significantly more support context
                new_role = "support"
        
        if self.test_mode:
            print(f"[TEST MODE] Detected role for conversation {conversation_id}: {new_role}")
            print(f"[TEST MODE] Sales keywords: {sales_count}, Support keywords: {support_count}")
        
        return new_role
    
    def get_role_context(self, conversation_id: str, message: str, history: List[Dict] = None) -> Dict:
        """
        Gets the context for a conversation based on its role.
        
        Args:
            conversation_id: The ID of the conversation
            message: The current message content
            history: Previous messages in the conversation
            
        Returns:
            A dictionary containing context information
        """
        # Detect the role if not already known
        role = self.detect_role(conversation_id, message, history)
        
        # Initialize context if it doesn't exist
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = {
                "role": role,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "sales_stage": "initial" if role == "sales" else None,
                "support_issue_type": "general" if role == "support" else None,
                "customer_info": {},
                "lead_info": {},
                "messages_count": 1
            }
        else:
            # Update existing context
            context = self.contexts[conversation_id]
            context["role"] = role
            context["last_updated"] = datetime.now().isoformat()
            context["messages_count"] += 1
            
            # Update role-specific context
            if role == "sales" and not context.get("sales_stage"):
                context["sales_stage"] = "initial"
            elif role == "support" and not context.get("support_issue_type"):
                context["support_issue_type"] = "general"
        
        # Extract customer information from message if possible
        self._extract_customer_info(conversation_id, message)
        
        # Update sales stage if in sales role
        if role == "sales":
            self._update_sales_stage(conversation_id, message, history)
        
        # Update support issue type if in support role
        if role == "support":
            self._update_support_issue_type(conversation_id, message, history)
        
        return self.contexts[conversation_id]
    
    def _extract_customer_info(self, conversation_id: str, message: str) -> None:
        """
        Extracts customer information from a message.
        
        Args:
            conversation_id: The ID of the conversation
            message: The message content
        """
        context = self.contexts[conversation_id]
        customer_info = context.get("customer_info", {})
        
        # Simple pattern matching for demonstration
        # In production, you would use more sophisticated NLP techniques
        
        # Look for email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails and not customer_info.get("email"):
            customer_info["email"] = emails[0]
        
        # Look for phone numbers (simple pattern)
        phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = re.findall(phone_pattern, message)
        if phones and not customer_info.get("phone"):
            customer_info["phone"] = phones[0]
        
        # Look for names (very simplistic approach)
        name_patterns = [
            r'(?:my name is|I am|I\'m) ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'(?:this is) ([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in name_patterns:
            names = re.findall(pattern, message)
            if names and not customer_info.get("name"):
                customer_info["name"] = names[0]
                break
        
        context["customer_info"] = customer_info
    
    def _update_sales_stage(self, conversation_id: str, message: str, history: List[Dict] = None) -> None:
        """
        Updates the sales stage based on the conversation.
        
        Args:
            conversation_id: The ID of the conversation
            message: The current message content
            history: Previous messages in the conversation
        """
        context = self.contexts[conversation_id]
        current_stage = context.get("sales_stage", "initial")
        
        # Define stage progression
        stages = ["initial", "discovery", "presentation", "objection_handling", "closing", "follow_up"]
        
        # Simple rules for stage progression
        if current_stage == "initial":
            # Move to discovery if customer is asking about specific services
            if any(keyword in message.lower() for keyword in ["what", "which", "how much", "tell me about", "options"]):
                context["sales_stage"] = "discovery"
        
        elif current_stage == "discovery":
            # Move to presentation if specific plan details are being discussed
            if any(keyword in message.lower() for keyword in ["details", "features", "benefits", "specific", "that plan"]):
                context["sales_stage"] = "presentation"
        
        elif current_stage == "presentation":
            # Move to objection handling if concerns are raised
            if any(keyword in message.lower() for keyword in ["expensive", "too much", "concern", "not sure", "competitor"]):
                context["sales_stage"] = "objection_handling"
        
        elif current_stage == "objection_handling":
            # Move to closing if customer shows buying signals
            if any(keyword in message.lower() for keyword in ["sign up", "get started", "purchase", "buy", "proceed"]):
                context["sales_stage"] = "closing"
        
        elif current_stage == "closing":
            # Move to follow up if purchase is complete
            if any(keyword in message.lower() for keyword in ["thank you", "received", "confirmation", "done"]):
                context["sales_stage"] = "follow_up"
    
    def _update_support_issue_type(self, conversation_id: str, message: str, history: List[Dict] = None) -> None:
        """
        Updates the support issue type based on the conversation.
        
        Args:
            conversation_id: The ID of the conversation
            message: The current message content
            history: Previous messages in the conversation
        """
        context = self.contexts[conversation_id]
        current_issue_type = context.get("support_issue_type", "general")
        
        # Define issue types
        issue_types = {
            "connectivity": ["can't connect", "no internet", "offline", "disconnected", "no signal"],
            "speed": ["slow", "speed", "bandwidth", "buffering", "lagging"],
            "billing": ["bill", "payment", "charge", "invoice", "overcharged", "credit"],
            "technical": ["router", "modem", "device", "setup", "configuration", "settings"],
            "account": ["password", "login", "account", "profile", "details", "information"]
        }
        
        # Check for issue type keywords
        for issue_type, keywords in issue_types.items():
            if any(keyword in message.lower() for keyword in keywords):
                context["support_issue_type"] = issue_type
                break
    
    def save_context(self, conversation_id: str, context: Dict) -> None:
        """
        Saves the context for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            context: The context to save
        """
        self.contexts[conversation_id] = context
        
        # In production, you would save to a database here
        if not self.test_mode:
            # Example database save (not implemented)
            pass
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """
        Gets the conversation history for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            A list of message dictionaries
        """
        # In test mode, return mock history
        if self.test_mode:
            if conversation_id not in self.contexts:
                return []
                
            # Generate mock history based on the context
            context = self.contexts[conversation_id]
            role = context.get("role", "support")
            
            if role == "sales":
                return self._generate_mock_sales_history(context)
            else:
                return self._generate_mock_support_history(context)
        
        # In production, you would retrieve from a database
        return []
    
    def _generate_mock_sales_history(self, context: Dict) -> List[Dict]:
        """Generates mock sales conversation history for testing"""
        sales_stage = context.get("sales_stage", "initial")
        messages = []
        
        # Create appropriate mock history based on sales stage
        if sales_stage == "initial":
            messages = [
                {"role": "customer", "content": "Hi, I'm interested in your internet services"},
                {"role": "agent", "content": "Hello! I'd be happy to tell you about our internet plans. What type of internet service are you looking for?"}
            ]
        elif sales_stage == "discovery":
            messages = [
                {"role": "customer", "content": "Hi, I'm interested in your internet services"},
                {"role": "agent", "content": "Hello! I'd be happy to tell you about our internet plans. What type of internet service are you looking for?"},
                {"role": "customer", "content": "I need something fast for streaming and gaming"},
                {"role": "agent", "content": "For streaming and gaming, I'd recommend our high-speed fiber plans. We have several options depending on your budget and speed requirements."}
            ]
        elif sales_stage in ["presentation", "objection_handling", "closing", "follow_up"]:
            messages = [
                {"role": "customer", "content": "Hi, I'm interested in your internet services"},
                {"role": "agent", "content": "Hello! I'd be happy to tell you about our internet plans. What type of internet service are you looking for?"},
                {"role": "customer", "content": "I need something fast for streaming and gaming"},
                {"role": "agent", "content": "For streaming and gaming, I'd recommend our high-speed fiber plans. We have several options depending on your budget and speed requirements."},
                {"role": "customer", "content": "What's your fastest plan and how much does it cost?"},
                {"role": "agent", "content": "Our fastest plan is our Fiber Ultra package with 1 Gbps download and 500 Mbps upload speeds for $89.99/month. It's perfect for gaming and 4K streaming."}
            ]
            
            if sales_stage in ["objection_handling", "closing", "follow_up"]:
                messages.extend([
                    {"role": "customer", "content": "That seems expensive compared to other providers"},
                    {"role": "agent", "content": "I understand your concern about the price. While our Fiber Ultra plan may seem higher priced, we offer consistent speeds even during peak hours and have no data caps, unlike many competitors."}
                ])
                
                if sales_stage in ["closing", "follow_up"]:
                    messages.extend([
                        {"role": "customer", "content": "That makes sense. How do I sign up?"},
                        {"role": "agent", "content": "Great! I can help you sign up right now. I'll just need some information from you to get started. Could you provide your full name, address, and preferred installation date?"}
                    ])
                    
                    if sales_stage == "follow_up":
                        messages.extend([
                            {"role": "customer", "content": "Thanks, I've completed the signup process"},
                            {"role": "agent", "content": "Excellent! You're all set. Your installation is scheduled for next Tuesday between 9 AM and 12 PM. Is there anything else you need help with today?"}
                        ])
        
        return messages
    
    def _generate_mock_support_history(self, context: Dict) -> List[Dict]:
        """Generates mock support conversation history for testing"""
        issue_type = context.get("support_issue_type", "general")
        messages = []
        
        # Create appropriate mock history based on issue type
        if issue_type == "general":
            messages = [
                {"role": "customer", "content": "Hi, I need some help"},
                {"role": "agent", "content": "Hello! I'm here to help. What seems to be the issue you're experiencing?"}
            ]
        elif issue_type == "connectivity":
            messages = [
                {"role": "customer", "content": "My internet is not working"},
                {"role": "agent", "content": "I'm sorry to hear that. Let's troubleshoot your connection issue. Have you tried restarting your router?"},
                {"role": "customer", "content": "Yes, I've already tried that"},
                {"role": "agent", "content": "Thank you for trying that first step. Let's check if there are any outages in your area. Could you please provide your account number or the address where service is installed?"}
            ]
        elif issue_type == "speed":
            messages = [
                {"role": "customer", "content": "My internet is really slow today"},
                {"role": "agent", "content": "I understand how frustrating slow internet can be. Let's check what might be causing this. Are you experiencing slowness on all devices or just one?"},
                {"role": "customer", "content": "It's slow on all devices"},
                {"role": "agent", "content": "Thank you for that information. Let's run a speed test to see what speeds you're currently getting. Could you go to speedtest.net and run a test, then share the results with me?"}
            ]
        elif issue_type == "billing":
            messages = [
                {"role": "customer", "content": "I think there's a mistake on my bill"},
                {"role": "agent", "content": "I'd be happy to look into that for you. Could you please provide your account number and let me know what specifically looks incorrect on your bill?"},
                {"role": "customer", "content": "I was charged for equipment I don't have"},
                {"role": "agent", "content": "I apologize for the incorrect charge. Let me check your account details to verify what equipment should be associated with your account."}
            ]
        elif issue_type == "technical":
            messages = [
                {"role": "customer", "content": "I need help setting up my new router"},
                {"role": "agent", "content": "I'd be happy to help you set up your new router. What model of router are you trying to set up?"},
                {"role": "customer", "content": "It's the one you provided, the NetGear AC1200"},
                {"role": "agent", "content": "Great, I'm familiar with the NetGear AC1200. Have you already connected it to your modem and power source?"}
            ]
        elif issue_type == "account":
            messages = [
                {"role": "customer", "content": "I need to reset my account password"},
                {"role": "agent", "content": "I can help you reset your password. For security purposes, could you please verify your account by providing your account number and the email address associated with your account?"},
                {"role": "customer", "content": "My account number is 12345 and email is customer@example.com"},
                {"role": "agent", "content": "Thank you for verifying your information. I'll send a password reset link to your email address. You should receive it within the next few minutes."}
            ]
        
        return messages

    def update_context(self, conversation_id: str, message: str, history: List[Dict] = None) -> Dict:
        """
        Updates the context for a conversation with a new message.
        
        Args:
            conversation_id: The ID of the conversation
            message: The new message content
            history: Previous messages in the conversation
            
        Returns:
            The updated context dictionary
        """
        # Get role-based context
        context = self.get_role_context(conversation_id, message, history)
        
        # Check for role transitions
        previous_role = context.get("previous_role")
        current_role = context.get("role")
        
        # If role has changed, record the transition
        if previous_role and previous_role != current_role:
            transitions = context.get("role_transitions", [])
            transitions.append({
                "from": previous_role,
                "to": current_role,
                "timestamp": datetime.now().isoformat()
            })
            context["role_transitions"] = transitions
        
        # Store current role as previous for next update
        context["previous_role"] = current_role
        
        # Update last message timestamp
        context["last_message_time"] = datetime.now().isoformat()
        
        if self.test_mode:
            print(f"[TEST MODE] Updated context for conversation {conversation_id}")
            print(f"[TEST MODE] Current role: {current_role}")
            if current_role == "sales":
                print(f"[TEST MODE] Sales stage: {context.get('sales_stage')}")
            else:
                print(f"[TEST MODE] Support issue type: {context.get('support_issue_type')}")
        
        return context
    
    def get_current_role(self, conversation_id: str) -> Optional[str]:
        """
        Gets the current role for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            "sales", "support", or None if conversation not found
        """
        if conversation_id in self.contexts:
            return self.contexts[conversation_id].get("role")
        return None
    
    def get_sales_stage(self, conversation_id: str) -> Optional[str]:
        """
        Gets the current sales stage for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The current sales stage or None if not applicable
        """
        if conversation_id in self.contexts and self.contexts[conversation_id].get("role") == "sales":
            return self.contexts[conversation_id].get("sales_stage")
        return None
    
    def get_support_issue_type(self, conversation_id: str) -> Optional[str]:
        """
        Gets the current support issue type for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The current support issue type or None if not applicable
        """
        if conversation_id in self.contexts and self.contexts[conversation_id].get("role") == "support":
            return self.contexts[conversation_id].get("support_issue_type")
        return None
    
    def get_customer_info(self, conversation_id: str) -> Dict:
        """
        Gets the customer information for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dictionary containing customer information
        """
        if conversation_id in self.contexts:
            return self.contexts[conversation_id].get("customer_info", {})
        return {}
    
    def set_customer_info(self, conversation_id: str, customer_info: Dict) -> None:
        """
        Sets or updates customer information for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            customer_info: Dictionary containing customer information
        """
        if conversation_id in self.contexts:
            existing_info = self.contexts[conversation_id].get("customer_info", {})
            # Update with new info
            existing_info.update(customer_info)
            self.contexts[conversation_id]["customer_info"] = existing_info
    
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """
        Gets a summary of the conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dictionary containing a summary of the conversation context
        """
        if conversation_id not in self.contexts:
            return {"error": "Conversation not found"}
        
        context = self.contexts[conversation_id]
        role = context.get("role", "unknown")
        
        summary = {
            "conversation_id": conversation_id,
            "role": role,
            "messages_count": context.get("messages_count", 0),
            "created_at": context.get("created_at"),
            "last_updated": context.get("last_updated"),
            "customer_info": context.get("customer_info", {})
        }
        
        # Add role-specific information
        if role == "sales":
            summary["sales_stage"] = context.get("sales_stage")
            summary["lead_info"] = context.get("lead_info", {})
        elif role == "support":
            summary["support_issue_type"] = context.get("support_issue_type")
            summary["resolution_status"] = context.get("resolution_status", "pending")
        
        # Add role transitions if any
        if "role_transitions" in context and context["role_transitions"]:
            summary["role_transitions"] = context["role_transitions"]
        
        return summary
    
    def reset_context(self, conversation_id: str) -> None:
        """
        Resets the context for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            if self.test_mode:
                print(f"[TEST MODE] Reset context for conversation {conversation_id}")
    
    def save_contexts(self, file_path: str) -> bool:
        """
        Saves all conversation contexts to a file (for test mode).
        
        Args:
            file_path: Path to save the contexts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.contexts, f, indent=2)
            return True
        except Exception as e:
            if self.test_mode:
                print(f"[TEST MODE] Error saving contexts: {str(e)}")
            return False
    
    def load_contexts(self, file_path: str) -> bool:
        """
        Loads conversation contexts from a file (for test mode).
        
        Args:
            file_path: Path to load the contexts from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                self.contexts = json.load(f)
            return True
        except Exception as e:
            if self.test_mode:
                print(f"[TEST MODE] Error loading contexts: {str(e)}")
            return False
