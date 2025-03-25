"""
Dual-role agent implementation for handling both sales and support queries.
"""
import os
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, Tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Import agent prompts
from agent_prompts import get_system_prompt

# Import reliability components
from logger_config import logger, llm_metrics
from reliability import LLMReliabilityWrapper
from prometheus_metrics import track_request, track_conversation
from semantic_cache import semantic_cache

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"]
)

# Initialize reliability-enhanced LLM
model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
llm_wrapper = LLMReliabilityWrapper(
    model=model_name,
    cache_enabled=os.getenv("ENABLE_SEMANTIC_CACHE", "true").lower() == "true",
    metrics_enabled=os.getenv("ENABLE_METRICS", "true").lower() == "true",
    fallback_response="I'm sorry, but I'm currently experiencing high demand. Please try again in a moment."
)

# Initialize OpenAI
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY", "test_key"),
    temperature=0.3,
    model_name=model_name
)

class DualRoleAgent:
    """
    Agent that can handle both sales and support roles.
    """
    
    def __init__(self, tools_config: Dict[str, List[Tool]]):
        """
        Initialize the dual-role agent with tools for each role.
        
        Args:
            tools_config: Dictionary mapping roles to their respective tools
        """
        self.tools_config = tools_config
        self.agent_graphs = {}
        self.memory = MemorySaver()
        
        # Initialize agent graphs for each role
        for role, tools in tools_config.items():
            self.agent_graphs[role] = self._create_agent_graph(role, tools)
            
        logger.info(
            "dual_role_agent_initialized",
            roles=list(tools_config.keys()),
            tools_count={role: len(tools) for role, tools in tools_config.items()}
        )
    
    def _create_agent_graph(self, role: str, tools: List[BaseTool]):
        """
        Create an agent graph for a specific role.
        
        Args:
            role: The role for the agent ("sales" or "support")
            tools: List of tools available to the agent
            
        Returns:
            An initialized LangGraph agent
        """
        # Create default context data with just the role
        default_context_data = {
            "role": role,
            "sales_stage": "initial" if role == "sales" else None,
            "support_issue_type": "general" if role == "support" else None,
            "customer_info": {},
            "entities": {}
        }
        
        # Get the appropriate system prompt based on the role
        system_prompt = get_system_prompt(role, default_context_data)
        
        # Create and return the agent graph
        return create_react_agent(
            llm,
            tools=tools,
            prompt=system_prompt,
            checkpointer=self.memory,
        )
    
    @track_request(endpoint_name="process_message")
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
        start_time = time.time()
        conversation_id = str(uuid.uuid4())
        metadata = {
            "conversation_id": conversation_id,
            "role": role,
            "message_length": len(message),
            "context_data_provided": context_data is not None
        }
        
        # Track conversation start
        track_conversation("started")
        
        logger.info(
            "processing_message",
            conversation_id=conversation_id,
            role=role,
            message_length=len(message),
            has_context_data=context_data is not None
        )
        
        # Extract entities from message
        entity_ids = self.extract_entity_ids(message)
        if entity_ids:
            logger.info(
                "entities_extracted",
                conversation_id=conversation_id,
                entities=entity_ids
            )
            metadata["extracted_entities"] = entity_ids
            
            # Add extracted entities to context data
            if context_data is None:
                context_data = {}
            if "entities" not in context_data:
                context_data["entities"] = {}
            context_data["entities"].update(entity_ids)
        
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
            cache_key += f":{hash(frozenset(context_data.items()))}"
        
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
        
        # Get the agent graph for the specified role
        agent_graph = self.agent_graphs[role]
        
        # Update the system prompt with context data if provided
        if context_data:
            # Ensure role is included in context_data
            if "role" not in context_data:
                context_data["role"] = role
                
            # Add default values for required fields if not present
            if role == "sales" and "sales_stage" not in context_data:
                context_data["sales_stage"] = "initial"
            elif role == "support" and "support_issue_type" not in context_data:
                context_data["support_issue_type"] = "general"
                
            # Update the system prompt
            system_prompt = get_system_prompt(role, context_data)
            
            # Create a unique thread ID for this conversation
            thread_id = conversation_id
            config = {"configurable": {"thread_id": thread_id}}
            
            # Create a human message from the input
            input_message = HumanMessage(content=message)
            
            # Process the message
            try:
                # Stream the response and get the last message
                response_messages = []
                for event in agent_graph.stream(
                    {"messages": [input_message]}, 
                    config, 
                    stream_mode="values"
                ):
                    response_messages = event["messages"]
                
                # Get the content of the last message
                if response_messages and len(response_messages) > 0:
                    response_content = response_messages[-1].content
                    
                    # Cache the response
                    semantic_cache.set(cache_key, response_content, metadata)
                    
                    # Track conversation completion
                    duration = time.time() - start_time
                    track_conversation("completed", duration, len(response_messages))
                    
                    # Update metadata
                    metadata["duration_seconds"] = duration
                    metadata["message_count"] = len(response_messages)
                    
                    logger.info(
                        "message_processed",
                        conversation_id=conversation_id,
                        role=role,
                        duration_seconds=duration,
                        message_count=len(response_messages),
                        response_length=len(response_content)
                    )
                    
                    return response_content, metadata
                else:
                    error_msg = "I'm sorry, I couldn't process your request."
                    
                    # Track conversation failure
                    track_conversation("failed")
                    
                    logger.warning(
                        "empty_response",
                        conversation_id=conversation_id,
                        role=role
                    )
                    
                    return error_msg, metadata
            except Exception as e:
                error_msg = f"I'm sorry, I encountered an error while processing your request. Please try again or contact customer support for assistance."
                
                # Track conversation failure
                track_conversation("failed")
                
                logger.error(
                    "processing_error",
                    conversation_id=conversation_id,
                    role=role,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                return error_msg, metadata
        
        # If no context data is provided, use a simpler approach
        try:
            # Create a unique thread ID for this conversation
            thread_id = conversation_id
            config = {"configurable": {"thread_id": thread_id}}
            
            # Create a human message from the input
            input_message = HumanMessage(content=message)
            
            # Process the message
            response_messages = []
            for event in agent_graph.stream(
                {"messages": [input_message]}, 
                config, 
                stream_mode="values"
            ):
                response_messages = event["messages"]
            
            # Get the content of the last message
            if response_messages and len(response_messages) > 0:
                response_content = response_messages[-1].content
                
                # Cache the response
                semantic_cache.set(cache_key, response_content, metadata)
                
                # Track conversation completion
                duration = time.time() - start_time
                track_conversation("completed", duration, len(response_messages))
                
                # Update metadata
                metadata["duration_seconds"] = duration
                metadata["message_count"] = len(response_messages)
                
                logger.info(
                    "message_processed",
                    conversation_id=conversation_id,
                    role=role,
                    duration_seconds=duration,
                    message_count=len(response_messages),
                    response_length=len(response_content)
                )
                
                return response_content, metadata
            else:
                error_msg = "I'm sorry, I couldn't process your request."
                
                # Track conversation failure
                track_conversation("failed")
                
                logger.warning(
                    "empty_response",
                    conversation_id=conversation_id,
                    role=role
                )
                
                return error_msg, metadata
        except Exception as e:
            error_msg = f"I'm sorry, I encountered an error while processing your request. Please try again or contact customer support for assistance."
            
            # Track conversation failure
            track_conversation("failed")
            
            logger.error(
                "processing_error",
                conversation_id=conversation_id,
                role=role,
                error=str(e),
                error_type=type(e).__name__
            )
            
            return error_msg, metadata
    
    def extract_entity_ids(self, message: str) -> Dict[str, str]:
        """
        Extract entity IDs from a message using regex patterns.
        
        Args:
            message: The message to extract entity IDs from
            
        Returns:
            Dictionary of entity IDs
        """
        import re
        
        entity_ids = {}
        
        # Extract customer ID (e.g., CUS-12345)
        customer_id_match = re.search(r'(?i)customer(?:\s+id)?[:\s]+([A-Z]+-\d+)', message)
        if customer_id_match:
            entity_ids['customer_id'] = customer_id_match.group(1)
        
        # Extract order ID (e.g., ORD-12345)
        order_id_match = re.search(r'(?i)order(?:\s+id)?[:\s]+([A-Z]+-\d+)', message)
        if order_id_match:
            entity_ids['order_id'] = order_id_match.group(1)
        
        # Extract device ID (e.g., DEV-12345)
        device_id_match = re.search(r'(?i)device(?:\s+id)?[:\s]+([A-Z]+-\d+)', message)
        if device_id_match:
            entity_ids['device_id'] = device_id_match.group(1)
        
        # Extract site ID (e.g., SITE-12345)
        site_id_match = re.search(r'(?i)site(?:\s+id)?[:\s]+([A-Z]+-\d+)', message)
        if site_id_match:
            entity_ids['site_id'] = site_id_match.group(1)
        
        return entity_ids
