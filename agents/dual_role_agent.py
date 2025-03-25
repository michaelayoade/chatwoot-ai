"""
Dual-role agent implementation for handling both sales and support queries.
"""
import os
from typing import Dict, List, Any, Optional
from langchain.agents import Tool, AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage

# Import agent prompts
from agent_prompts import get_system_prompt

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"]
)

# Initialize OpenAI
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY", "test_key"),
    temperature=0.3,
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
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
        self.agent_executors = {}
        
        # Initialize agent executors for each role
        for role, tools in tools_config.items():
            self.agent_executors[role] = self._create_agent_executor(role, tools)
    
    def _create_agent_executor(self, role: str, tools: List[Tool]) -> AgentExecutor:
        """
        Create an agent executor for a specific role.
        
        Args:
            role: The role for the agent ("sales" or "support")
            tools: List of tools available to the agent
            
        Returns:
            An initialized AgentExecutor
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
        
        # Create a memory buffer for the conversation
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create and return the agent executor
        return initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            agent_kwargs={
                "system_message": system_prompt
            }
        )
    
    def process_message(self, message: str, role: str, context_data: Optional[Dict] = None) -> str:
        """
        Process a message using the appropriate agent based on the role.
        
        Args:
            message: The message to process
            role: The role to use ("sales" or "support")
            context_data: Optional context data to include in the prompt
            
        Returns:
            The agent's response
        """
        if role not in self.agent_executors:
            raise ValueError(f"Invalid role: {role}. Must be one of: {list(self.agent_executors.keys())}")
        
        # Get the agent executor for the specified role
        agent_executor = self.agent_executors[role]
        
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
            agent_executor.agent.llm_chain.prompt.messages[0] = SystemMessage(content=system_prompt)
        
        # Process the message and return the response
        try:
            response = agent_executor.run(input=message)
            return response
        except Exception as e:
            print(f"Error processing message with {role} agent: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your request. Please try again or contact customer support for assistance."
    
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
