import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import requests
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage
from langchain_core.messages import AIMessage, HumanMessage

# Load environment variables
load_dotenv()

# Initialize OpenAI
llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4-turbo",
)

# Initialize Conversation Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ----- System Integration Tools -----

class ERPNextTool:
    """Tool for interacting with ERPNext to get business information."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = self._get_authenticated_session()
    
    def _get_authenticated_session(self):
        session = requests.Session()
        login_data = {
            'usr': self.api_key,
            'pwd': self.api_secret
        }
        session.post(f"{self.base_url}/api/method/login", data=login_data)
        return session
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get the status of an order by ID"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/resource/Sales Order/{order_id}"
            )
            response.raise_for_status()
            order_data = response.json().get("data", {})
            
            return {
                "order_id": order_id,
                "status": order_data.get("status", "Unknown"),
                "customer_name": order_data.get("customer_name", "Unknown"),
                "total_amount": order_data.get("grand_total", 0),
                "delivery_date": order_data.get("delivery_date", "Not specified"),
                "items": [item.get("item_name") for item in order_data.get("items", [])]
            }
        except Exception as e:
            return {"error": f"Failed to retrieve order information: {str(e)}"}
    
    def get_customer_info(self, customer_id: str) -> Dict:
        """Get customer information by ID"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/resource/Customer/{customer_id}"
            )
            response.raise_for_status()
            customer_data = response.json().get("data", {})
            
            return {
                "customer_id": customer_id,
                "name": customer_data.get("customer_name", "Unknown"),
                "email": customer_data.get("email_id", "Not provided"),
                "phone": customer_data.get("mobile_no", "Not provided"),
                "customer_type": customer_data.get("customer_type", "Unknown"),
                "customer_group": customer_data.get("customer_group", "Unknown"),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve customer information: {str(e)}"}


class SplynxTool:
    """Tool for interacting with Splynx for internet service information."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.auth_token = self._get_auth_token()
    
    def _get_auth_token(self) -> str:
        auth_url = f"{self.base_url}/api/auth/admin"
        headers = {
            "Content-Type": "application/json"
        }
        auth_data = {
            "auth_type": "api_key",
            "login": self.api_key,
            "password": self.api_secret
        }
        
        response = requests.post(auth_url, headers=headers, json=auth_data)
        response.raise_for_status()
        return response.json().get("access_token")
    
    def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/api/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return {"error": "Unsupported method"}
        
        response.raise_for_status()
        return response.json()
    
    def get_customer_internet_status(self, customer_id: str) -> Dict:
        """Get the internet service status for a customer"""
        try:
            response = self._make_api_request(f"customers/customer/{customer_id}")
            services = self._make_api_request(f"customers/customer/{customer_id}/internet")
            
            customer_data = response.get("customer", {})
            service_data = services.get("services", [])
            
            active_services = [s for s in service_data if s.get("status") == "active"]
            
            return {
                "customer_id": customer_id,
                "name": customer_data.get("name", "Unknown"),
                "status": customer_data.get("status", "Unknown"),
                "balance": customer_data.get("balance", 0),
                "active_services": len(active_services),
                "services": [
                    {
                        "service_id": s.get("id"),
                        "plan": s.get("tariff_name", "Unknown"),
                        "status": s.get("status", "Unknown"),
                        "speed": f"{s.get('download', 0)}/{s.get('upload', 0)} Mbps"
                    }
                    for s in service_data
                ]
            }
        except Exception as e:
            return {"error": f"Failed to retrieve internet service information: {str(e)}"}
    
    def get_payment_history(self, customer_id: str, limit: int = 5) -> Dict:
        """Get recent payment history for a customer"""
        try:
            payments = self._make_api_request(f"customers/customer/{customer_id}/payments?limit={limit}")
            
            return {
                "customer_id": customer_id,
                "payments": [
                    {
                        "payment_id": p.get("id"),
                        "date": p.get("date"),
                        "amount": p.get("amount"),
                        "comment": p.get("comment", "No comment"),
                        "type": p.get("type", "Unknown")
                    }
                    for p in payments.get("payments", [])
                ]
            }
        except Exception as e:
            return {"error": f"Failed to retrieve payment history: {str(e)}"}


class UNMSTool:
    """Tool for interacting with UNMS (Ubiquiti Network Management System)."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def _make_api_request(self, endpoint: str) -> Dict:
        headers = {
            "X-Auth-Token": self.api_key,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/api/v2.1/{endpoint}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_device_status(self, device_id: str) -> Dict:
        """Get the status of a network device by ID"""
        try:
            response = self._make_api_request(f"devices/{device_id}")
            
            return {
                "device_id": device_id,
                "name": response.get("name", "Unknown"),
                "model": response.get("model", "Unknown"),
                "status": response.get("status", "Unknown"),
                "ip_address": response.get("ipAddress", "Unknown"),
                "uptime": response.get("uptime", "Unknown"),
                "firmware": response.get("firmwareVersion", "Unknown"),
                "last_seen": response.get("lastSeen", "Unknown"),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve device information: {str(e)}"}
    
    def get_service_outages(self, limit: int = 5) -> Dict:
        """Get recent service outages"""
        try:
            response = self._make_api_request(f"outages?limit={limit}")
            
            return {
                "outages": [
                    {
                        "outage_id": o.get("id"),
                        "start_time": o.get("startTime"),
                        "end_time": o.get("endTime", "Ongoing"),
                        "affected_sites": o.get("affectedSites", 0),
                        "affected_devices": o.get("affectedDevices", 0),
                        "status": o.get("status", "Unknown"),
                        "severity": o.get("severity", "Unknown")
                    }
                    for o in response.get("items", [])
                ]
            }
        except Exception as e:
            return {"error": f"Failed to retrieve outage information: {str(e)}"}


# Initialize our tools
erp_tool = ERPNextTool(
    api_key=os.getenv("ERPNEXT_API_KEY"),
    api_secret=os.getenv("ERPNEXT_API_SECRET"),
    base_url=os.getenv("ERPNEXT_BASE_URL")
)

splynx_tool = SplynxTool(
    api_key=os.getenv("SPLYNX_API_KEY"),
    api_secret=os.getenv("SPLYNX_API_SECRET"),
    base_url=os.getenv("SPLYNX_BASE_URL")
)

unms_tool = UNMSTool(
    api_key=os.getenv("UNMS_API_KEY"),
    base_url=os.getenv("UNMS_BASE_URL")
)

# ----- Create LangChain Tools -----

tools = [
    Tool(
        name="order_status",
        func=lambda order_id: erp_tool.get_order_status(order_id),
        description="Use this to get information about an order by its ID. Input should be the order ID."
    ),
    Tool(
        name="customer_info",
        func=lambda customer_id: erp_tool.get_customer_info(customer_id),
        description="Use this to get general customer information by customer ID. Input should be the customer ID."
    ),
    Tool(
        name="internet_status",
        func=lambda customer_id: splynx_tool.get_customer_internet_status(customer_id),
        description="Use this to get information about a customer's internet service status. Input should be the customer ID."
    ),
    Tool(
        name="payment_history",
        func=lambda customer_id: splynx_tool.get_payment_history(customer_id),
        description="Use this to get a customer's recent payment history. Input should be the customer ID."
    ),
    Tool(
        name="network_device",
        func=lambda device_id: unms_tool.get_device_status(device_id),
        description="Use this to get status information about a specific network device. Input should be the device ID."
    ),
    Tool(
        name="service_outages",
        func=lambda: unms_tool.get_service_outages(),
        description="Use this to get information about recent service outages. No input needed."
    ),
]

# ----- Create LangChain Agent -----

# Define the agent prompt
agent_prompt = PromptTemplate.from_template(
    """You are a helpful customer service assistant that helps customers with their queries.
    You have access to various systems to provide accurate information.
    
    Respond professionally and with empathy to customer questions. If you need specific information to answer a question,
    use the appropriate tool to get the information you need.
    
    {chat_history}
    Question: {input}
    {agent_scratchpad}
    """
)

# Create the agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=agent_prompt
)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# ----- Chatwoot Integration -----

class ChatwootHandler:
    """Handler for Chatwoot webhooks and API integration."""
    
    def __init__(self, api_key: str, account_id: str, base_url: str):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url
        self.headers = {
            "api_access_token": self.api_key,
            "Content-Type": "application/json"
        }
    
    def send_message(self, conversation_id: str, message: str) -> Dict:
        """Send a message to a Chatwoot conversation"""
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        payload = {
            "content": message,
            "message_type": "outgoing"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def process_webhook(self, webhook_data: Dict) -> Dict:
        """Process incoming webhook data from Chatwoot"""
        try:
            # Extract relevant information from the webhook
            event_type = webhook_data.get("event")
            
            # We only care about incoming messages
            if event_type != "message_created" or webhook_data.get("message_type") != "incoming":
                return {"status": "ignored", "reason": "Not an incoming message"}
            
            conversation_id = webhook_data.get("conversation", {}).get("id")
            message_content = webhook_data.get("content")
            sender_id = webhook_data.get("sender", {}).get("id")
            
            # Process the message with our LangChain agent
            agent_response = agent_executor.invoke({
                "input": message_content
            })
            
            response_text = agent_response.get("output")
            
            # Send the response back to Chatwoot
            self.send_message(conversation_id, response_text)
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "response": response_text
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ----- Flask Web Server to Handle Webhooks -----

from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Chatwoot handler
chatwoot_handler = ChatwootHandler(
    api_key=os.getenv("CHATWOOT_API_KEY"),
    account_id=os.getenv("CHATWOOT_ACCOUNT_ID"),
    base_url=os.getenv("CHATWOOT_BASE_URL")
)

@app.route('/webhook/chatwoot', methods=['POST'])
def chatwoot_webhook():
    """Handle incoming webhooks from Chatwoot"""
    webhook_data = request.json
    result = chatwoot_handler.process_webhook(webhook_data)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})


# ----- Utility Functions -----

def extract_entity_ids(text: str) -> Dict[str, str]:
    """
    Extract potential entity IDs from customer messages
    This is a simple implementation - in production you'd want more robust extraction
    """
    import re
    
    # Define patterns for different types of IDs
    patterns = {
        "order_id": r"order[:\s#]*([A-Za-z0-9\-]+)",
        "customer_id": r"customer[:\s#]*([A-Za-z0-9\-]+)",
        "device_id": r"device[:\s#]*([A-Za-z0-9\-]+)"
    }
    
    results = {}
    for entity_type, pattern in patterns.items():
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            results[entity_type] = matches.group(1)
    
    return results


# ----- Main Application Entry Point -----

if __name__ == "__main__":
    # Load environment variables from .env file
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=debug)