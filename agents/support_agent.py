"""
Support agent implementation for handling support queries.
"""
import os
import time
import uuid
import re
import sys
from typing import Dict, List, Any, Optional, Tuple, Mapping, Union
import hashlib
import json

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from logger_config import logger
from prometheus_metrics import track_request
from semantic_cache import semantic_cache

# Check if we're in a testing environment
testing_mode = (
    'unittest' in sys.modules or
    'pytest' in sys.modules or
    os.environ.get('TESTING', 'False').lower() in ('true', '1', 't') or
    os.environ.get('CI', 'False').lower() in ('true', '1', 't')
)

# Create a function to get the LLM
def get_llm():
    if testing_mode:
        from unittest.mock import MagicMock
        
        # Create a base mock that handles any method call
        mock_llm = MagicMock()
        
        # Specify only the methods we know are directly called
        mock_llm.invoke.return_value = "This is a mock response from the LLM"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.bind.return_value = mock_llm
        
        # Add any other specific method behaviors needed
        mock_llm._llm_type = "mock"
        
        return mock_llm
    else:
        from langchain_deepseek import ChatDeepSeek
        
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        # Remove 'Bearer ' prefix if present
        if deepseek_api_key.startswith("Bearer "):
            deepseek_api_key = deepseek_api_key[7:]
        
        return ChatDeepSeek(
            api_key=deepseek_api_key,
            temperature=0.3,
            model_name=model_name
        )

# Initialize the LLM
llm = get_llm()

class SupportAgent:
    """Agent that handles support queries."""
    
    def __init__(self, tools: List[Any]):
        """
        Initialize the support agent with tools.
        
        Args:
            tools: List of tools available to the agent
        """
        self.tools = tools
        self.agent_executor = self._create_agent_executor()
        
        logger.info(
            "support_agent_initialized",
            tools_count=len(tools)
        )
    
    def _create_agent_executor(self):
        """
        Create an agent executor for the support role.
        
        Returns:
            An initialized agent executor
        """
        # Create the agent with the appropriate tools and system prompt
        system_prompt = "You are a helpful assistant specializing in technical support for an ISP. You help customers with troubleshooting, service issues, and technical questions."
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_openai_tools_agent(
            llm,
            self.tools,
            prompt
        )
        
        # Create the executor
        return AgentExecutor(agent=agent, tools=self.tools)
    
    def process_message(self, message: str, context_data: Optional[Dict] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Process a message using the support agent.
        
        Args:
            message: The message to process
            context_data: Optional context data for the conversation
            
        Returns:
            A tuple of (response, metadata)
        """
        start_time = time.time()
        conversation_id = str(uuid.uuid4())
        if context_data and "conversation_id" in context_data:
            conversation_id = context_data["conversation_id"]
        
        logger.info(
            "processing_support_message",
            conversation_id=conversation_id,
            message_length=len(message)
        )
        
        track_request("process_support_message")
        
        # Create a unique key for caching based on the message and context
        context_hash = hashlib.sha256(
            json.dumps(context_data, sort_keys=True).encode()
        ).hexdigest() if context_data else ""
        
        cache_key = f"support:{message}:{context_hash}"
        
        # Try to get from cache first
        try:
            cached_response = semantic_cache.get(cache_key)
            if cached_response:
                logger.info(
                    "cache_hit",
                    cache="semantic_responses",
                    key=cache_key
                )
                duration = time.time() - start_time
                # Extract just the response text from the cached dictionary
                response_text = cached_response.get("response", "I'm sorry, I couldn't process your request.")
                return response_text, {"cached": True, "role": "support", "duration_seconds": duration}
            
            logger.info(
                "cache_miss",
                cache="semantic_responses",
                key=cache_key
            )
        except Exception as e:
            logger.error(
                "cache_error",
                error=str(e),
                error_type=type(e).__name__
            )
        
        # Extract entity IDs if needed
        entity_ids = {}
        if message:
            try:
                entity_ids = self.extract_entity_ids(message)
            except Exception as e:
                logger.error(
                    "entity_extraction_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        # Prepare input for the agent
        agent_input = {
            "input": message
        }
        
        # Add context data if available
        if context_data:
            agent_input["context"] = context_data
        
        # Add entity IDs if available
        if entity_ids:
            agent_input["entities"] = entity_ids
        
        # Process the message
        try:
            agent_response = self.agent_executor.invoke(agent_input)
            response = agent_response.get("output", "I'm sorry, I couldn't process your request.")
            
            # Cache the response
            try:
                semantic_cache.set(
                    cache_key,
                    {
                        "response": response,
                        "timestamp": time.time(),
                        "role": "support"
                    }
                )
            except Exception as e:
                logger.error(
                    "cache_set_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
            
            # Calculate processing time and prepare metadata
            duration = time.time() - start_time
            metadata = {
                "role": "support",
                "processing_time": duration,
                "cached": False,
                "entities": entity_ids,
                "duration_seconds": duration
            }
            
            logger.info(
                "support_message_processed",
                conversation_id=conversation_id,
                duration_seconds=duration,
                response_length=len(response)
            )
            
            return response, metadata
            
        except Exception as e:
            # Log the error
            duration = time.time() - start_time
            logger.error(
                "agent_error",
                conversation_id=conversation_id,
                role="support",
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return a fallback response
            return "I'm sorry, but I encountered an error while processing your request. Please try again or contact customer support for assistance.", {
                "role": "support",
                "error": str(e),
                "processing_time": duration,
                "duration_seconds": duration
            }
    
    def extract_entity_ids(self, message: str) -> Dict[str, str]:
        """
        Extract entity IDs from a message using regex patterns.
        
        Args:
            message: The message to extract entity IDs from
            
        Returns:
            Dictionary of entity IDs
        """
        entity_ids = {}
        
        # Extract customer ID
        customer_id_match = re.search(r'customer[_\s]?id[:\s]+([a-zA-Z0-9-]+)', message, re.IGNORECASE)
        if customer_id_match:
            entity_ids['customer_id'] = customer_id_match.group(1)
        
        # Extract ticket ID
        ticket_id_match = re.search(r'ticket[_\s]?id[:\s]+([a-zA-Z0-9-]+)', message, re.IGNORECASE)
        if ticket_id_match:
            entity_ids['ticket_id'] = ticket_id_match.group(1)
        
        # Extract device ID
        device_id_match = re.search(r'device[_\s]?id[:\s]+([a-zA-Z0-9-]+)', message, re.IGNORECASE)
        if device_id_match:
            entity_ids['device_id'] = device_id_match.group(1)
        
        return entity_ids
