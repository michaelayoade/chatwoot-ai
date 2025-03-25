"""
Dual-role agent implementation for handling both sales and support queries.
"""
import os
import time
import json
import re
from typing import Dict, List, Any, Tuple, Optional
import hashlib
import uuid

import langchain
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.runnables import RunnablePassthrough

from logger_config import logger, llm_metrics
from reliability import LLMReliabilityWrapper
from prometheus_metrics import track_request, track_conversation
from semantic_cache import semantic_cache

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("DEEPSEEK_API_KEY") in [None, "", "your_deepseek_api_key"]
)

# Initialize reliability-enhanced LLM
model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
llm_wrapper = LLMReliabilityWrapper(
    model=model_name,
    cache_enabled=os.getenv("ENABLE_SEMANTIC_CACHE", "true").lower() == "true",
    metrics_enabled=os.getenv("ENABLE_METRICS", "true").lower() == "true",
    fallback_response="I'm sorry, but I'm currently experiencing high demand. Please try again in a moment."
)

# Initialize Deepseek
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
# Remove 'Bearer ' prefix if present
if deepseek_api_key.startswith("Bearer "):
    deepseek_api_key = deepseek_api_key[7:]

llm = ChatDeepSeek(
    api_key=deepseek_api_key,
    temperature=0.3,
    model_name=model_name
)

class DualRoleAgent:
    """Agent that can handle both sales and support roles."""
    
    def __init__(self, tools_config: Dict[str, List[Any]]):
        """
        Initialize the dual-role agent with tools for each role.
        
        Args:
            tools_config: Dictionary mapping roles to their respective tools
        """
        self.tools_config = tools_config
        self.agent_graphs = {}
        
        # Initialize agent graphs for each role
        for role, tools in tools_config.items():
            self.agent_graphs[role] = self._create_agent_graph(role, tools)
            
        logger.info(
            "dual_role_agent_initialized",
            roles=list(tools_config.keys()),
            tools_count={role: len(tools) for role, tools in tools_config.items()}
        )
    
    def _create_agent_graph(self, role: str, tools: List[Any]):
        """
        Create an agent graph for a specific role.
        
        Args:
            role: The role for the agent ("sales" or "support")
            tools: List of tools available to the agent
            
        Returns:
            An initialized LangGraph agent
        """
        # Create the agent with the appropriate tools and system prompt
        system_prompt = f"You are a helpful assistant specializing in {role} for an ISP."
        
        # Create the agent
        agent = create_openai_tools_agent(
            llm,
            tools,
            system_prompt
        )
        
        # Create the executor
        return AgentExecutor(agent=agent, tools=tools)
    
    def process_message(self, message: str, role: str, context_data: Optional[Dict] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Process a message using the appropriate agent based on the role.
        
        Args:
            message: The message to process
            role: The role to use ("sales" or "support")
            context_data: Optional context data to include in the prompt
            
        Returns:
            Tuple of (agent's response, metadata)
        """
        # Start tracking the request
        start_time = time.time()
        conversation_id = context_data.get("conversation_id", str(uuid.uuid4())) if context_data else str(uuid.uuid4())
        track_request("process_message")
        
        # Initialize metadata
        metadata = {
            "conversation_id": conversation_id,
            "role": role,
            "message_length": len(message),
            "timestamp": time.time()
        }
        
        # Extract entities from message
        entity_ids = self.extract_entity_ids(message)
        if entity_ids:
            # Convert all entity_ids values to strings to avoid unhashable type errors
            string_entity_ids = {}
            for key, value in entity_ids.items():
                if isinstance(value, dict):
                    # Convert nested dictionary to a flattened structure with string keys and values
                    for k, v in value.items():
                        string_entity_ids[f"{key}_{k}"] = str(v)
                else:
                    string_entity_ids[key] = str(value)
            
            logger.info(
                "entities_extracted",
                conversation_id=conversation_id,
                entities=string_entity_ids
            )
            metadata["extracted_entities"] = string_entity_ids
            
            # Add extracted entities to context data
            if context_data is None:
                context_data = {}
            if "entities" not in context_data:
                context_data["entities"] = {}
            
            # Update with string entities
            context_data["entities"].update(string_entity_ids)
        
        # Check if role is valid
        if role not in self.agent_graphs:
            error_msg = f"Invalid role: {role}. Must be one of: {list(self.agent_graphs.keys())}"
            logger.error(
                "invalid_role",
                conversation_id=conversation_id,
                role=role,
                valid_roles=list(self.agent_graphs.keys())
            )
            track_conversation("failed")
            return error_msg, metadata
        
        # Check if we can use semantic cache for this query
        cache_key = f"{role}:{message}"
        if context_data:
            # Create a stringified version of context_data for hashing
            # Convert all values to strings to avoid unhashable type errors
            try:
                flatten_dict = {}
                for k, v in context_data.items():
                    if isinstance(v, dict):
                        # For nested dictionaries, create a flattened representation
                        for inner_k, inner_v in v.items():
                            flatten_dict[f"{k}.{inner_k}"] = str(inner_v)
                    else:
                        flatten_dict[k] = str(v)
                # Sort the items to ensure consistent cache keys
                sorted_items = sorted(flatten_dict.items())
                # Join key-value pairs with a delimiter
                context_str = "|".join([f"{k}={v}" for k, v in sorted_items])
                # Add hash of the stringified context to the cache key
                cache_key += f":{hashlib.sha256(context_str.encode()).hexdigest()}"
            except Exception as e:
                # If there's any error in hash generation, we can safely ignore it
                # as it's just for caching, and proceed without a context-specific cache
                logger.warning(
                    "cache_key_generation_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        cached_response = semantic_cache.get(cache_key)
        if cached_response:
            logger.info(
                "cache_hit",
                conversation_id=conversation_id,
                role=role,
                cache_type=cached_response.get("cache_info", {}).get("semantic_match", False) and "semantic" or "exact"
            )
            
            duration = time.time() - start_time
            track_conversation("completed", duration)
            
            metadata["cache_hit"] = True
            metadata["duration_seconds"] = duration
            
            return cached_response["response"], metadata
        
        logger.info(
            "cache_miss",
            cache="semantic_responses",
            key=cache_key
        )
        
        # Prepare the input for the agent
        agent_input = {"input": message}
        
        # Add context data if available
        if context_data:
            # Ensure all values in context_data are strings to avoid serialization issues
            safe_context = {}
            for k, v in context_data.items():
                if isinstance(v, dict):
                    # Handle nested dictionaries
                    safe_context[k] = {str(inner_k): str(inner_v) for inner_k, inner_v in v.items()}
                else:
                    safe_context[k] = str(v) if v is not None else ""
            
            agent_input["context"] = safe_context
        
        try:
            # Call the agent
            agent_response = self.agent_graphs[role].invoke(agent_input)
            
            # Extract the response
            response = agent_response.get("output", "I'm sorry, but I couldn't process your request.")
            
            # Cache the response
            semantic_cache.add(
                cache_key,
                {
                    "response": response,
                    "timestamp": time.time(),
                    "role": role
                }
            )
            
            # Calculate duration
            duration = time.time() - start_time
            track_conversation("completed", duration)
            
            # Update metadata
            metadata["duration_seconds"] = duration
            metadata["cache_hit"] = False
            
            return response, metadata
            
        except Exception as e:
            # Log error
            logger.error(
                "agent_error",
                conversation_id=conversation_id,
                role=role,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Calculate duration
            duration = time.time() - start_time
            track_conversation("failed", duration)
            
            # Update metadata
            metadata["duration_seconds"] = duration
            metadata["error"] = str(e)
            metadata["error_type"] = type(e).__name__
            
            # Return error message
            return f"I'm sorry, but I encountered an error while processing your request: {str(e)}", metadata
    
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
        customer_id_match = re.search(r'customer[_\s]?id[:\s]+([a-zA-Z0-9]+)', message, re.IGNORECASE)
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
