"""
Main integration module for the LangChain-Chatwoot integration.
This module ties together the tools, agents, and handlers.
"""
import os
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import tools
from tools.erp_tool import ERPNextTool
from tools.splynx_tool import SplynxTool
from tools.unms_tool import UNMSTool

# Import handlers
from handlers.chatwoot_handler import ChatwootHandler

# Import agents
from agents.sales_agent import SalesAgent
from agents.support_agent import SupportAgent

# Import LangChain components
from langchain.agents import Tool

# Import reliability components
from logger_config import logger
from api_circuit_breaker import erp_circuit, splynx_circuit, unms_circuit
from rate_limiter import erp_rate_limiter, splynx_rate_limiter, unms_rate_limiter
from reliability import APIReliabilityWrapper
from prometheus_metrics import track_conversation

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("ERPNEXT_API_KEY") in [None, "", "your_erpnext_username"] or
    os.getenv("SPLYNX_API_KEY") in [None, "", "your_splynx_api_key"] or
    os.getenv("UNMS_API_KEY") in [None, "", "your_unms_api_key"]
)

logger.info(f"running_mode", test_mode=TEST_MODE)

# Create API reliability wrappers
erp_api = APIReliabilityWrapper(
    api_name="erpnext",
    circuit=erp_circuit,
    rate_limiter=erp_rate_limiter,
    metrics_enabled=True
)

splynx_api = APIReliabilityWrapper(
    api_name="splynx",
    circuit=splynx_circuit,
    rate_limiter=splynx_rate_limiter,
    metrics_enabled=True
)

unms_api = APIReliabilityWrapper(
    api_name="unms",
    circuit=unms_circuit,
    rate_limiter=unms_rate_limiter,
    metrics_enabled=True
)

# Initialize our tools
erp_tool = ERPNextTool(
    api_key=os.getenv("ERPNEXT_API_KEY", "test_key"),
    api_secret=os.getenv("ERPNEXT_API_SECRET", "test_secret"),
    base_url=os.getenv("ERPNEXT_BASE_URL", "https://erp.example.com")
)

splynx_tool = SplynxTool(
    api_key=os.getenv("SPLYNX_API_KEY", "test_key"),
    api_secret=os.getenv("SPLYNX_API_SECRET", "test_secret"),
    base_url=os.getenv("SPLYNX_BASE_URL", "https://splynx.example.com")
)

unms_tool = UNMSTool(
    api_key=os.getenv("UNMS_API_KEY", "test_key"),
    base_url=os.getenv("UNMS_BASE_URL", "https://unms.example.com")
)

# Wrap tool functions with reliability wrappers
def wrap_erp_function(func, endpoint):
    """Wrap ERP function with reliability features"""
    def wrapper(*args, **kwargs):
        return erp_api.call(func, *args, **kwargs)
    return wrapper

def wrap_splynx_function(func, endpoint):
    """Wrap Splynx function with reliability features"""
    def wrapper(*args, **kwargs):
        return splynx_api.call(func, *args, **kwargs)
    return wrapper

def wrap_unms_function(func, endpoint):
    """Wrap UNMS function with reliability features"""
    def wrapper(*args, **kwargs):
        return unms_api.call(func, *args, **kwargs)
    return wrapper

# Create LangChain tools with reliability wrappers
# Sales tools
erp_tool_customer_info = Tool(
    name="get_customer_info",
    func=wrap_erp_function(erp_tool.get_customer_info, "customers"),
    description="Get information about a customer by their ID"
)

erp_tool_service_plans = Tool(
    name="get_service_plans",
    func=wrap_erp_function(erp_tool.get_service_plans, "service_plans"),
    description="Get available internet service plans, optionally filtered by type (fiber, dsl, wireless)"
)

erp_tool_promotions = Tool(
    name="get_promotions",
    func=wrap_erp_function(erp_tool.get_promotions, "promotions"),
    description="Get current promotions and special offers"
)

erp_tool_plan_details = Tool(
    name="get_plan_details",
    func=wrap_erp_function(erp_tool.get_plan_details, "plan_details"),
    description="Get detailed information about a specific internet plan by its ID"
)

erp_tool_order_status = Tool(
    name="get_order_status",
    func=wrap_erp_function(erp_tool.get_order_status, "order_status"),
    description="Check the status of an order by its ID"
)

# Support tools
splynx_tool_internet_status = Tool(
    name="get_internet_status",
    func=wrap_splynx_function(splynx_tool.get_customer_internet_status, "internet_status"),
    description="Get the current status of a customer's internet service by their ID"
)

splynx_tool_payment_history = Tool(
    name="get_payment_history",
    func=wrap_splynx_function(splynx_tool.get_payment_history, "payment_history"),
    description="Get recent payment history for a customer by their ID"
)

unms_tool_device_status = Tool(
    name="get_device_status",
    func=wrap_unms_function(unms_tool.get_device_status, "device_status"),
    description="Get the status of a network device by its ID"
)

unms_tool_site_status = Tool(
    name="get_site_status",
    func=wrap_unms_function(unms_tool.get_site_status, "site_status"),
    description="Get the status of a network site by its ID"
)

unms_tool_outage_info = Tool(
    name="get_outage_info",
    func=wrap_unms_function(unms_tool.get_outage_info, "outage_info"),
    description="Get information about current network outages, optionally filtered by location"
)

# Create tools configuration
sales_tools = [
    erp_tool_customer_info,
    erp_tool_service_plans,
    erp_tool_promotions,
    erp_tool_plan_details,
    erp_tool_order_status
]

support_tools = [
    splynx_tool_internet_status,
    splynx_tool_payment_history,
    unms_tool_device_status,
    unms_tool_site_status,
    unms_tool_outage_info
]

# Initialize the agents
sales_agent = SalesAgent(sales_tools)
support_agent = SupportAgent(support_tools)

# Initialize Chatwoot handler
chatwoot_handler = ChatwootHandler(
    api_key=os.getenv("CHATWOOT_API_KEY", "test_key"),
    account_id=os.getenv("CHATWOOT_ACCOUNT_ID", "1"),
    base_url=os.getenv("CHATWOOT_BASE_URL", "https://chatwoot.example.com"),
    context_manager=None  # Will be set by the app.py
)

def extract_entity_ids(message: str) -> Dict[str, str]:
    """
    Extract entity IDs from a message using regex patterns.
    
    Args:
        message: The message to extract entity IDs from
        
    Returns:
        Dictionary of entity IDs
    """
    entity_ids = {}
    
    # Extract customer ID (e.g., CUS-12345)
    # Updated pattern to match "My customer ID is CUS-54321"
    customer_id_match = re.search(r'(?i)customer(?:\s+id)?(?:\s+is)?[:\s]+([A-Z]+-\d+)', message)
    if customer_id_match:
        entity_ids['customer_id'] = customer_id_match.group(1)
    
    # Extract order ID (e.g., ORD-12345)
    # Updated pattern to match "I'm having issues with my order ORD-98765"
    # Fixed by using a single regex pattern with (?i) only at the beginning
    order_id_match = re.search(r'(?i)(?:order|ORD)(?:\s+id)?(?:\s+is)?[:\s]+([A-Z]+-\d+)', message)
    if order_id_match:
        entity_ids['order_id'] = order_id_match.group(1)
    else:
        # Try alternative pattern for "with my order ORD-98765" format
        alt_order_match = re.search(r'(?i)(?:with|for|my)\s+order\s+([A-Z]+-\d+)', message)
        if alt_order_match:
            entity_ids['order_id'] = alt_order_match.group(1)
    
    # Extract device ID (e.g., DEV-12345)
    device_id_match = re.search(r'(?i)device(?:\s+id)?(?:\s+is)?[:\s]+([A-Z]+-\d+)', message)
    if device_id_match:
        entity_ids['device_id'] = device_id_match.group(1)
    
    # Extract site ID (e.g., SITE-12345)
    site_id_match = re.search(r'(?i)site(?:\s+id)?(?:\s+is)?[:\s]+([A-Z]+-\d+)', message)
    if site_id_match:
        entity_ids['site_id'] = site_id_match.group(1)
    
    return entity_ids

def process_message(message: str, conversation_id: str, context_manager=None) -> str:
    """
    Process a message using the appropriate agent based on the conversation context.
    
    Args:
        message: The message to process
        conversation_id: The ID of the conversation
        context_manager: The conversation context manager
        
    Returns:
        The agent's response as a string
    """
    try:
        print(f"Starting process_message with conversation_id: {conversation_id}")
        start_time = time.time()
        metadata = {
            "conversation_id": conversation_id,
            "message_length": len(message),
            "timestamp": time.time()
        }
        
        # Extract entity IDs from the message
        try:
            print("Extracting entity IDs from message...")
            entity_ids = extract_entity_ids(message)
            print(f"Extracted entity_ids: {entity_ids}")
            
            # Convert all entity_ids values to strings to avoid unhashable type errors
            string_entity_ids = {}
            for key, value in entity_ids.items():
                if isinstance(value, dict):
                    # Convert nested dictionary to a flattened structure with string keys and values
                    for k, v in value.items():
                        string_entity_ids[f"{key}_{k}"] = str(v)
                else:
                    string_entity_ids[key] = str(value)
                    
            print(f"Converted to string_entity_ids: {string_entity_ids}")
        except Exception as e:
            print(f"Error extracting entity IDs: {str(e)}")
            import traceback
            print(traceback.format_exc())
            string_entity_ids = {}
        
        # Determine the role based on the conversation context
        try:
            print("Determining role from conversation context...")
            role = "support"  # Default role
            if context_manager:
                role = context_manager.get_current_role(conversation_id)
                metadata["role"] = role
                
                # Get the conversation context
                context_data = context_manager.get_conversation_summary(conversation_id)
                print(f"Got context_data with keys: {list(context_data.keys() if context_data else [])}")
                
                # Add entity IDs to the context
                if string_entity_ids:
                    if "entities" not in context_data:
                        context_data["entities"] = {}
                    
                    # Add each entity ID to the context - no need to process nested dictionaries
                    # as we've already flattened them above
                    for key, value in string_entity_ids.items():
                        context_data["entities"][key] = value
                    
                    # Update the context with the new entities
                    try:
                        print(f"Updating context with entities: {string_entity_ids}")
                        context_manager.update_entities(conversation_id, string_entity_ids)
                    except Exception as e:
                        print(f"Error updating context with entities: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
            else:
                print("No context manager provided, using default role")
                context_data = {
                    "role": role,
                    "entities": string_entity_ids
                }
                
            print(f"Using role: {role}")
            
            logger.info(
                "processing_message",
                conversation_id=conversation_id,
                role=role,
                message_length=len(message),
                context_data_keys=list(context_data.keys()) if context_data else []
            )
            
            # Process the message
            print(f"Calling agent.process_message with role={role}")
            
            # Add defensive copying to prevent modification of shared data structures
            safe_context_data = {}
            if context_data:
                for key, value in context_data.items():
                    if key == "entities" and isinstance(value, dict):
                        # Create a new dictionary with string keys and values
                        safe_context_data[key] = {str(k): str(v) for k, v in value.items()}
                    elif isinstance(value, dict):
                        # Create a deep copy of nested dictionaries
                        safe_context_data[key] = {str(k): str(v) for k, v in value.items()}
                    else:
                        # For non-dictionary values, just use the string value
                        safe_context_data[key] = str(value) if value is not None else ""
            
            print(f"Safe context data: {safe_context_data}")
            
            # Use the appropriate agent based on the role
            if role == "sales":
                response, agent_metadata = sales_agent.process_message(message, safe_context_data)
            else:  # Default to support
                response, agent_metadata = support_agent.process_message(message, safe_context_data)
            
            # Update metadata with agent metadata
            if isinstance(agent_metadata, dict):
                metadata.update(agent_metadata)
            
            # Calculate processing time
            duration = time.time() - start_time
            metadata["processing_time"] = duration
            
            logger.info(
                "message_processed",
                conversation_id=conversation_id,
                role=role,
                duration_seconds=duration,
                response_length=len(response)
            )
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            import traceback
            print(traceback.format_exc())
            logger.error(
                "message_processing_error",
                conversation_id=conversation_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            return f"I'm sorry, but I encountered an error while processing your request. Please try again or contact customer support for assistance."
            
    except Exception as e:
        print(f"Unexpected error in process_message: {str(e)}")
        import traceback
        print(traceback.format_exc())
        logger.error(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__
        )
        
        return "I'm sorry, but I encountered an unexpected error. Please try again later."
