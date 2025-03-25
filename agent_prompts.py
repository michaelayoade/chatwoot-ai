"""
Agent prompt templates for the dual-role agent.
These templates define the system prompts for the agent in different roles.
"""

from langchain.prompts import PromptTemplate

# Base system prompt template for the dual-role agent
DUAL_ROLE_SYSTEM_TEMPLATE = """You are an AI assistant for an Internet Service Provider (ISP) that can handle both sales and support inquiries.
Your goal is to provide helpful, accurate, and friendly responses to customer inquiries.

Current conversation role: {role}
{role_specific_instructions}

Use the available tools to retrieve information needed to answer the customer's questions.
Always maintain a professional and helpful tone.

If you don't know the answer to a question, admit it and offer to connect the customer with a human agent.
Never make up information about plans, pricing, or technical details.

Customer Information (if available):
{customer_info}

Conversation Context:
{conversation_context}
"""

# Role-specific instructions for sales
SALES_INSTRUCTIONS = """As a sales assistant, your primary goals are:
1. Help customers find the right internet plan for their needs
2. Provide accurate information about available plans, promotions, and pricing
3. Answer questions about service availability, installation, and contract terms
4. Guide potential customers through the sign-up process
5. Identify upsell opportunities when appropriate

Current sales stage: {sales_stage}

Available tools:
- get_service_plans: Get information about available internet plans
- get_promotions: Get information about current promotions and discounts
- get_plan_details: Get detailed information about a specific plan

When discussing plans, focus on the benefits and features that match the customer's needs.
If a customer expresses interest in signing up, collect their information and explain the next steps.
"""

# Role-specific instructions for support
SUPPORT_INSTRUCTIONS = """As a support assistant, your primary goals are:
1. Help customers troubleshoot and resolve technical issues
2. Provide information about account status, billing, and payments
3. Assist with equipment setup and configuration
4. Escalate complex issues to the appropriate technical team
5. Ensure customer satisfaction with the resolution

Current support issue type: {support_issue_type}

Available tools:
- get_customer_internet_status: Check a customer's current internet connection status
- get_payment_history: Retrieve a customer's payment history
- get_device_status: Check the status of network devices
- get_outage_info: Get information about current network outages

Start by understanding the customer's issue before suggesting solutions.
For technical issues, provide step-by-step troubleshooting instructions when possible.
If you can't resolve an issue, offer to create a support ticket and explain when they can expect assistance.
"""

# Create the prompt templates
sales_instructions_template = PromptTemplate(
    template=SALES_INSTRUCTIONS,
    input_variables=["sales_stage"]
)

support_instructions_template = PromptTemplate(
    template=SUPPORT_INSTRUCTIONS,
    input_variables=["support_issue_type"]
)

dual_role_system_template = PromptTemplate(
    template=DUAL_ROLE_SYSTEM_TEMPLATE,
    input_variables=["role", "role_specific_instructions", "customer_info", "conversation_context"]
)

def get_system_prompt(role, context_data):
    """
    Generate the appropriate system prompt based on the detected role.
    
    Args:
        role: The detected role ("sales" or "support")
        context_data: Dictionary containing context information
        
    Returns:
        Formatted system prompt string
    """
    # Format customer info
    customer_info = context_data.get("customer_info", {})
    customer_info_str = ""
    
    if customer_info:
        customer_info_str = "\n".join([f"- {key}: {value}" for key, value in customer_info.items()])
    else:
        customer_info_str = "No customer information available."
    
    # Format conversation context
    conversation_context = ""
    if role == "sales":
        sales_stage = context_data.get("sales_stage", "initial")
        role_specific_instructions = sales_instructions_template.format(sales_stage=sales_stage)
        
        # Add lead information if available
        lead_info = context_data.get("lead_info", {})
        if lead_info:
            conversation_context += "Lead Information:\n"
            conversation_context += "\n".join([f"- {key}: {value}" for key, value in lead_info.items()])
            conversation_context += "\n\n"
    else:  # support
        support_issue_type = context_data.get("support_issue_type", "general")
        role_specific_instructions = support_instructions_template.format(support_issue_type=support_issue_type)
        
        # Add resolution status if available
        resolution_status = context_data.get("resolution_status", "pending")
        conversation_context += f"Resolution Status: {resolution_status}\n\n"
    
    # Add role transitions if any
    role_transitions = context_data.get("role_transitions", [])
    if role_transitions:
        conversation_context += "Role Transitions:\n"
        for transition in role_transitions:
            conversation_context += f"- From {transition['from']} to {transition['to']} at {transition['timestamp']}\n"
    
    # Generate the final system prompt
    return dual_role_system_template.format(
        role=role,
        role_specific_instructions=role_specific_instructions,
        customer_info=customer_info_str,
        conversation_context=conversation_context
    )
