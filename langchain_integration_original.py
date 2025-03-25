import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import requests
from langchain.agents import Tool, AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage
from langchain_core.messages import AIMessage, HumanMessage
from agent_prompts import get_system_prompt

# Load environment variables
load_dotenv()

# Check if we're in test mode (when API keys are missing or placeholder values)
TEST_MODE = (
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("ERPNEXT_API_KEY") in [None, "", "your_erpnext_username"] or
    os.getenv("SPLYNX_API_KEY") in [None, "", "your_splynx_api_key"] or
    os.getenv("UNMS_API_KEY") in [None, "", "your_unms_api_key"]
)

print(f"Running in {'TEST MODE' if TEST_MODE else 'PRODUCTION MODE'}")

# Initialize OpenAI
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY", "test_key"),
    temperature=0.3,
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
)

# Initialize Conversation Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ----- System Integration Tools -----

class ERPNextTool:
    """Tool for interacting with ERPNext API to get business information."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.test_mode = TEST_MODE
        self.headers = {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json"
        }
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status information for a specific order"""
        if self.test_mode:
            print(f"[TEST MODE] Getting order status for order ID: {order_id}")
            # Return mock data for testing
            return {
                "order_id": order_id,
                "status": "Processing",
                "created_date": "2023-05-10",
                "items": [
                    {"item": "Fiber Internet 100Mbps", "qty": 1, "price": 59.99},
                    {"item": "WiFi Router", "qty": 1, "price": 9.99}
                ],
                "total": 69.98,
                "estimated_delivery": "2023-05-15"
            }
            
        url = f"{self.base_url}/api/resource/Sales Order/{order_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            return {"error": f"Failed to retrieve order status: {str(e)}"}
    
    def get_customer_info(self, customer_id: str) -> Dict:
        """Get general information about a customer"""
        if self.test_mode:
            print(f"[TEST MODE] Getting customer info for customer ID: {customer_id}")
            # Return mock data for testing
            return {
                "customer_id": customer_id,
                "name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St, Anytown, USA",
                "customer_since": "2022-01-15",
                "current_plan": "Fiber Internet 100Mbps",
                "billing_cycle": "Monthly",
                "next_billing_date": "2023-06-01"
            }
            
        url = f"{self.base_url}/api/resource/Customer/{customer_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            return {"error": f"Failed to retrieve customer information: {str(e)}"}
    
    def get_service_plans(self, service_type: str = None) -> Dict:
        """
        Get available service plans from ERPNext items
        
        Args:
            service_type: Optional filter for service type (e.g., "fiber", "dsl", "wireless")
            
        Returns:
            Dictionary containing available service plans
        """
        if self.test_mode:
            print(f"[TEST MODE] Getting service plans, filter: {service_type}")
            # Return mock data for testing
            all_plans = {
                "fiber": [
                    {
                        "plan_id": "FIB-50",
                        "name": "Fiber Essential",
                        "speed_down": 50,
                        "speed_up": 25,
                        "price": 49.99,
                        "description": "Basic fiber internet for everyday browsing and streaming",
                        "features": ["No data caps", "Free installation", "Basic technical support"]
                    },
                    {
                        "plan_id": "FIB-100",
                        "name": "Fiber Plus",
                        "speed_down": 100,
                        "speed_up": 50,
                        "price": 69.99,
                        "description": "Fast fiber internet for multiple users and HD streaming",
                        "features": ["No data caps", "Free installation", "24/7 technical support", "Free WiFi router"]
                    },
                    {
                        "plan_id": "FIB-500",
                        "name": "Fiber Pro",
                        "speed_down": 500,
                        "speed_up": 250,
                        "price": 89.99,
                        "description": "Ultra-fast fiber internet for heavy streaming and gaming",
                        "features": ["No data caps", "Free installation", "24/7 priority support", "Free WiFi 6 router"]
                    },
                    {
                        "plan_id": "FIB-1000",
                        "name": "Fiber Ultra",
                        "speed_down": 1000,
                        "speed_up": 500,
                        "price": 109.99,
                        "description": "Lightning-fast fiber internet for the ultimate online experience",
                        "features": ["No data caps", "Free installation", "24/7 priority support", "Free WiFi 6 router", "Static IP address"]
                    }
                ],
                "dsl": [
                    {
                        "plan_id": "DSL-10",
                        "name": "DSL Basic",
                        "speed_down": 10,
                        "speed_up": 1,
                        "price": 29.99,
                        "description": "Reliable DSL internet for basic browsing",
                        "features": ["No contract", "Free modem", "Email support"]
                    },
                    {
                        "plan_id": "DSL-25",
                        "name": "DSL Plus",
                        "speed_down": 25,
                        "speed_up": 3,
                        "price": 39.99,
                        "description": "Faster DSL internet for streaming and browsing",
                        "features": ["No contract", "Free modem", "Phone and email support"]
                    }
                ],
                "wireless": [
                    {
                        "plan_id": "WIR-25",
                        "name": "Wireless Basic",
                        "speed_down": 25,
                        "speed_up": 5,
                        "price": 49.99,
                        "description": "Wireless internet for rural areas",
                        "features": ["No phone line required", "Free installation", "Basic support"]
                    },
                    {
                        "plan_id": "WIR-50",
                        "name": "Wireless Plus",
                        "speed_down": 50,
                        "speed_up": 10,
                        "price": 69.99,
                        "description": "Faster wireless internet for rural areas",
                        "features": ["No phone line required", "Free installation", "24/7 support", "Free router"]
                    }
                ]
            }
            
            # Filter by service type if provided
            if service_type and service_type.lower() in all_plans:
                return {"plans": all_plans[service_type.lower()]}
            
            # Otherwise return all plans
            all_plan_list = []
            for plan_type in all_plans.values():
                all_plan_list.extend(plan_type)
            
            return {"plans": all_plan_list}
        
        # In production mode, query ERPNext
        filters = {}
        if service_type:
            filters["service_type"] = service_type
            
        url = f"{self.base_url}/api/resource/Item"
        params = {
            "filters": json.dumps(filters),
            "fields": json.dumps([
                "name", "item_name", "description", "standard_rate", 
                "service_type", "download_speed", "upload_speed", "features"
            ])
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transform ERPNext data to match our API format
            plans = []
            for item in data.get("data", []):
                plan = {
                    "plan_id": item.get("name"),
                    "name": item.get("item_name"),
                    "speed_down": item.get("download_speed"),
                    "speed_up": item.get("upload_speed"),
                    "price": item.get("standard_rate"),
                    "description": item.get("description"),
                    "features": item.get("features", "").split("\n") if item.get("features") else []
                }
                plans.append(plan)
                
            return {"plans": plans}
        except Exception as e:
            return {"error": f"Failed to retrieve service plans: {str(e)}"}
    
    def get_promotions(self) -> Dict:
        """
        Get current promotions from ERPNext pricing rules
        
        Returns:
            Dictionary containing available promotions
        """
        if self.test_mode:
            print("[TEST MODE] Getting current promotions")
            # Return mock data for testing
            return {
                "promotions": [
                    {
                        "promo_id": "PROMO-SPRING",
                        "name": "Spring Special",
                        "description": "Get 3 months free when you sign up for any Fiber plan",
                        "discount_type": "Free Months",
                        "discount_value": 3,
                        "eligible_plans": ["FIB-50", "FIB-100", "FIB-500", "FIB-1000"],
                        "start_date": "2023-03-01",
                        "end_date": "2023-05-31"
                    },
                    {
                        "promo_id": "PROMO-UPGRADE",
                        "name": "Upgrade Discount",
                        "description": "Existing customers get $10 off monthly when upgrading to a faster plan",
                        "discount_type": "Monthly Discount",
                        "discount_value": 10,
                        "eligible_plans": ["FIB-500", "FIB-1000"],
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31"
                    },
                    {
                        "promo_id": "PROMO-BUNDLE",
                        "name": "TV Bundle",
                        "description": "Add TV service to any internet plan and save 20% on both",
                        "discount_type": "Percentage",
                        "discount_value": 20,
                        "eligible_plans": ["FIB-50", "FIB-100", "FIB-500", "FIB-1000", "DSL-10", "DSL-25"],
                        "start_date": "2023-02-15",
                        "end_date": "2023-06-30"
                    }
                ]
            }
            
        # In production mode, query ERPNext
        url = f"{self.base_url}/api/resource/Pricing Rule"
        params = {
            "fields": json.dumps([
                "name", "title", "description", "discount_type", "discount_amount",
                "applicable_for", "valid_from", "valid_upto", "items"
            ])
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transform ERPNext data to match our API format
            promotions = []
            for rule in data.get("data", []):
                promo = {
                    "promo_id": rule.get("name"),
                    "name": rule.get("title"),
                    "description": rule.get("description"),
                    "discount_type": rule.get("discount_type"),
                    "discount_value": rule.get("discount_amount"),
                    "eligible_plans": [item.get("item_code") for item in rule.get("items", [])],
                    "start_date": rule.get("valid_from"),
                    "end_date": rule.get("valid_upto")
                }
                promotions.append(promo)
                
            return {"promotions": promotions}
        except Exception as e:
            return {"error": f"Failed to retrieve promotions: {str(e)}"}
    
    def get_plan_details(self, plan_id: str) -> Dict:
        """
        Get detailed information about a specific plan
        
        Args:
            plan_id: The ID of the plan to retrieve
            
        Returns:
            Dictionary containing plan details
        """
        if self.test_mode:
            print(f"[TEST MODE] Getting plan details for plan ID: {plan_id}")
            # Return mock data for testing
            plan_details = {
                "FIB-50": {
                    "plan_id": "FIB-50",
                    "name": "Fiber Essential",
                    "service_type": "fiber",
                    "speed_down": 50,
                    "speed_up": 25,
                    "price": 49.99,
                    "setup_fee": 0,
                    "contract_length": 12,
                    "early_termination_fee": 99,
                    "description": "Basic fiber internet for everyday browsing and streaming",
                    "features": [
                        "No data caps",
                        "Free installation",
                        "Basic technical support"
                    ],
                    "recommended_for": [
                        "Small households (1-2 people)",
                        "Light internet users",
                        "Email and social media",
                        "Standard definition streaming"
                    ],
                    "equipment": [
                        {
                            "name": "Standard WiFi Router",
                            "monthly_fee": 0,
                            "purchase_option": 79.99
                        }
                    ],
                    "available_promotions": ["PROMO-SPRING", "PROMO-BUNDLE"]
                },
                "FIB-100": {
                    "plan_id": "FIB-100",
                    "name": "Fiber Plus",
                    "service_type": "fiber",
                    "speed_down": 100,
                    "speed_up": 50,
                    "price": 69.99,
                    "setup_fee": 0,
                    "contract_length": 12,
                    "early_termination_fee": 99,
                    "description": "Fast fiber internet for multiple users and HD streaming",
                    "features": [
                        "No data caps",
                        "Free installation",
                        "24/7 technical support",
                        "Free WiFi router"
                    ],
                    "recommended_for": [
                        "Medium households (2-4 people)",
                        "Multiple devices",
                        "HD video streaming",
                        "Light gaming"
                    ],
                    "equipment": [
                        {
                            "name": "Advanced WiFi Router",
                            "monthly_fee": 0,
                            "purchase_option": 99.99
                        }
                    ],
                    "available_promotions": ["PROMO-SPRING", "PROMO-BUNDLE"]
                },
                "FIB-500": {
                    "plan_id": "FIB-500",
                    "name": "Fiber Pro",
                    "service_type": "fiber",
                    "speed_down": 500,
                    "speed_up": 250,
                    "price": 89.99,
                    "setup_fee": 0,
                    "contract_length": 12,
                    "early_termination_fee": 99,
                    "description": "Ultra-fast fiber internet for heavy streaming and gaming",
                    "features": [
                        "No data caps",
                        "Free installation",
                        "24/7 priority support",
                        "Free WiFi 6 router"
                    ],
                    "recommended_for": [
                        "Large households (4+ people)",
                        "Multiple HD/4K streams",
                        "Online gaming",
                        "Work from home"
                    ],
                    "equipment": [
                        {
                            "name": "WiFi 6 Router",
                            "monthly_fee": 0,
                            "purchase_option": 149.99
                        }
                    ],
                    "available_promotions": ["PROMO-SPRING", "PROMO-UPGRADE", "PROMO-BUNDLE"]
                },
                "FIB-1000": {
                    "plan_id": "FIB-1000",
                    "name": "Fiber Ultra",
                    "service_type": "fiber",
                    "speed_down": 1000,
                    "speed_up": 500,
                    "price": 109.99,
                    "setup_fee": 0,
                    "contract_length": 12,
                    "early_termination_fee": 99,
                    "description": "Lightning-fast fiber internet for the ultimate online experience",
                    "features": [
                        "No data caps",
                        "Free installation",
                        "24/7 priority support",
                        "Free WiFi 6 router",
                        "Static IP address"
                    ],
                    "recommended_for": [
                        "Power users",
                        "Multiple 4K streams",
                        "Competitive gaming",
                        "Large file uploads/downloads",
                        "Smart home with many devices"
                    ],
                    "equipment": [
                        {
                            "name": "Premium WiFi 6 Router",
                            "monthly_fee": 0,
                            "purchase_option": 199.99
                        }
                    ],
                    "available_promotions": ["PROMO-SPRING", "PROMO-UPGRADE", "PROMO-BUNDLE"]
                }
            }
            
            if plan_id in plan_details:
                return plan_details[plan_id]
            else:
                return {"error": f"Plan ID {plan_id} not found"}
        
        # In production mode, query ERPNext
        url = f"{self.base_url}/api/resource/Item/{plan_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            item_data = response.json().get("data", {})
            
            # Get available promotions for this plan
            promotions_response = self.get_promotions()
            available_promotions = []
            if "promotions" in promotions_response:
                for promo in promotions_response["promotions"]:
                    if plan_id in promo.get("eligible_plans", []):
                        available_promotions.append(promo["promo_id"])
            
            # Transform ERPNext data to match our API format
            plan = {
                "plan_id": item_data.get("name"),
                "name": item_data.get("item_name"),
                "service_type": item_data.get("service_type"),
                "speed_down": item_data.get("download_speed"),
                "speed_up": item_data.get("upload_speed"),
                "price": item_data.get("standard_rate"),
                "setup_fee": item_data.get("setup_fee", 0),
                "contract_length": item_data.get("contract_length", 12),
                "early_termination_fee": item_data.get("early_termination_fee", 99),
                "description": item_data.get("description"),
                "features": item_data.get("features", "").split("\n") if item_data.get("features") else [],
                "recommended_for": item_data.get("recommended_for", "").split("\n") if item_data.get("recommended_for") else [],
                "equipment": [],  # Would need additional API call to get equipment details
                "available_promotions": available_promotions
            }
            
            return plan
        except Exception as e:
            return {"error": f"Failed to retrieve plan details: {str(e)}"}

class SplynxTool:
    """Tool for interacting with Splynx for internet service information."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.test_mode = TEST_MODE or os.getenv("TEST_MODE", "").lower() == "true"
        self.auth_token = None if self.test_mode else self._get_auth_token()
    
    def _get_auth_token(self):
        """Get authentication token from Splynx API"""
        if self.test_mode:
            return "test_token"
            
        auth_url = f"{self.base_url}/api/auth/admin"
        auth_data = {
            "auth_type": "api_key",
            "key": self.api_key,
            "secret": self.api_secret
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(auth_url, headers=headers, json=auth_data)
            response.raise_for_status()
            return response.json().get("token")
        except Exception as e:
            print(f"Error getting Splynx auth token: {str(e)}")
            return "test_token"  # Fallback to test token on error
    
    def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None):
        """Make an API request to Splynx"""
        if self.test_mode:
            # Return mock data for testing
            if "internet/services" in endpoint:
                return {
                    "status": "active",
                    "plan": "Fiber 100Mbps",
                    "ip_address": "192.168.1.100",
                    "last_online": "2023-03-24T15:30:45Z",
                    "signal_strength": "Excellent",
                    "download_speed": "95.2 Mbps",
                    "upload_speed": "48.7 Mbps"
                }
            elif "finance/payments" in endpoint:
                return [
                    {
                        "id": "PAY-001",
                        "date": "2023-03-15",
                        "amount": 89.99,
                        "status": "completed",
                        "method": "credit_card"
                    },
                    {
                        "id": "PAY-002",
                        "date": "2023-02-15",
                        "amount": 89.99,
                        "status": "completed",
                        "method": "credit_card"
                    }
                ]
            return {"message": "Mock data for testing"}
            
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making Splynx API request: {str(e)}")
            # Return mock data on error
            return {"error": str(e), "message": "Error retrieving data"}
    
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
    
    def get_payment_history(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get recent payment history for a customer"""
        if self.test_mode:
            return [
                {
                    "id": f"payment-{i}",
                    "date": f"2025-0{i}-01",
                    "amount": 89.99,
                    "status": "completed",
                    "method": "credit_card"
                } for i in range(1, min(limit + 1, 6))
            ]
        
        try:
            endpoint = f"customers/{customer_id}/payments?limit={limit}"
            response = self._make_api_request(endpoint)
            return response.get("payments", [])
        except Exception as e:
            return {"error": f"Failed to retrieve payment history: {str(e)}"}


class UNMSTool:
    """Tool for interacting with UNMS (Ubiquiti Network Management System)."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.test_mode = TEST_MODE or os.getenv("TEST_MODE", "").lower() == "true"
    
    def _make_api_request(self, endpoint: str) -> Dict:
        if self.test_mode:
            # Return mock data based on the endpoint
            if "devices" in endpoint:
                device_id = endpoint.split("/")[-1]
                return {
                    "id": device_id,
                    "identification": {
                        "name": f"Test Device {device_id}",
                        "model": "UniFi Switch Pro 24",
                        "site": "Main Office"
                    },
                    "overview": {
                        "status": "active",
                        "uptime": "15 days",
                        "cpu": 12,
                        "memory": 35,
                        "firmware": "6.5.2"
                    },
                    "interfaces": [
                        {
                            "name": "eth0",
                            "status": "connected",
                            "speed": "1 Gbps"
                        },
                        {
                            "name": "eth1",
                            "status": "connected",
                            "speed": "1 Gbps"
                        }
                    ]
                }
            elif "sites" in endpoint:
                site_id = endpoint.split("/")[-1]
                return {
                    "id": site_id,
                    "name": f"Site {site_id}",
                    "location": "123 Main St",
                    "status": "online",
                    "devices_count": 15,
                    "clients_count": 45
                }
            return {}
            
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
                "name": response.get("identification", {}).get("name", "Unknown"),
                "model": response.get("identification", {}).get("model", "Unknown"),
                "status": response.get("overview", {}).get("status", "Unknown"),
                "ip_address": response.get("identification", {}).get("ipAddress", "Unknown"),
                "uptime": response.get("overview", {}).get("uptime", "Unknown"),
                "firmware": response.get("overview", {}).get("firmwareVersion", "Unknown"),
                "last_seen": response.get("overview", {}).get("lastSeen", "Unknown"),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve device information: {str(e)}"}
    
    def get_site_status(self, site_id: str) -> Dict:
        """Get the status of a network site by ID"""
        if self.test_mode:
            print(f"[TEST MODE] Getting site status for site ID: {site_id}")
            # Return mock data for testing
            return {
                "site_id": site_id,
                "name": "Main Office",
                "status": "operational",
                "device_count": 15,
                "online_devices": 14,
                "offline_devices": 1,
                "bandwidth_usage": "45.7 Mbps",
                "last_outage": "2023-04-28T14:22:00Z",
                "location": "123 Main Street, City"
            }
            
        url = f"{self.base_url}/api/v2.1/sites/{site_id}"
        
        try:
            response = requests.get(url, headers={"X-Auth-Token": self.api_key, "Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to retrieve site status: {str(e)}"}
    
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
    
    def get_outage_info(self, location: str = None) -> Dict:
        """
        Get information about current network outages
        
        Args:
            location: Optional location or area code to filter outages
            
        Returns:
            Dictionary containing outage information
        """
        if self.test_mode:
            if location and location.lower() in ["downtown", "central", "10001"]:
                return {
                    "outages": [
                        {
                            "id": "OUT-001",
                            "location": "Downtown Area",
                            "start_time": "2025-03-25T06:30:00Z",
                            "estimated_resolution": "2025-03-25T10:30:00Z",
                            "status": "in_progress",
                            "affected_customers": 120,
                            "description": "Fiber cut due to construction work",
                            "updates": [
                                {
                                    "timestamp": "2025-03-25T07:15:00Z",
                                    "message": "Technicians on site, assessing damage"
                                },
                                {
                                    "timestamp": "2025-03-25T08:00:00Z",
                                    "message": "Repair work in progress"
                                }
                            ]
                        }
                    ],
                    "total_outages": 1
                }
            else:
                return {
                    "outages": [],
                    "total_outages": 0
                }
        
        endpoint = "outages"
        if location:
            endpoint += f"?location={location}"
        
        return self._make_api_request(endpoint)


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
    
    def process_webhook(self, webhook_data: Dict):
        """Process incoming webhook data from Chatwoot"""
        if self.test_mode:
            print(f"[TEST MODE] Processing webhook: {webhook_data}")
            return {"status": "success", "message": "Webhook processed in test mode"}
            
        try:
            # Extract relevant information from the webhook
            event_type = webhook_data.get("event")
            conversation_id = webhook_data.get("conversation", {}).get("id")
            message = webhook_data.get("message", {}).get("content", "")
            sender_type = webhook_data.get("message", {}).get("sender_type")
            
            # Only process messages from users, not from agents or bots
            if event_type == "message_created" and sender_type == "user" and message:
                # Update conversation context if context manager is available
                if self.context_manager:
                    self.context_manager.update_context(conversation_id, message)
                    
                    # Tag conversation based on detected role
                    current_role = self.context_manager.get_current_role(conversation_id)
                    if current_role:
                        self.tag_conversation(conversation_id, current_role)
                
                # Process the message with LangChain agent
                # This will be implemented in the main application
                
            return {"status": "success", "message": "Webhook processed"}
        except Exception as e:
            return {"error": f"Failed to process webhook: {str(e)}"}
    
    def send_message(self, conversation_id: str, message: str):
        """Send a message to a Chatwoot conversation"""
        if self.test_mode:
            print(f"[TEST MODE] Sending message to conversation {conversation_id}: {message}")
            return {"status": "success", "message": "Message sent in test mode"}
            
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
            return {"error": f"Failed to send message: {str(e)}"}
    
    def tag_conversation(self, conversation_id: str, tag_name: str):
        """Tag a conversation with a specific label"""
        if self.test_mode:
            print(f"[TEST MODE] Tagging conversation {conversation_id} with: {tag_name}")
            return {"status": "success", "message": f"Conversation tagged with {tag_name} in test mode"}
            
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/labels"
        payload = {
            "labels": [tag_name]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to tag conversation: {str(e)}"}
    
    def get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[Dict]:
        """Get the message history for a conversation"""
        if self.test_mode:
            print(f"[TEST MODE] Getting history for conversation {conversation_id}, limit: {limit}")
            # Return mock conversation history
            return [
                {
                    "id": 1001,
                    "content": "Hello, I'm interested in upgrading my internet plan.",
                    "sender_type": "user",
                    "created_at": "2023-05-15T10:30:00Z"
                },
                {
                    "id": 1002,
                    "content": "I'd be happy to help you with that! What plan are you currently on?",
                    "sender_type": "agent",
                    "created_at": "2023-05-15T10:31:00Z"
                },
                {
                    "id": 1003,
                    "content": "I have the 50Mbps fiber plan, but I need something faster for working from home.",
                    "sender_type": "user",
                    "created_at": "2023-05-15T10:32:00Z"
                }
            ]
            
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            print(f"Failed to get conversation history: {str(e)}")
            return []
    
    def update_conversation_status(self, conversation_id: str, status: str):
        """Update the status of a conversation (open, resolved, pending)"""
        if self.test_mode:
            print(f"[TEST MODE] Updating conversation {conversation_id} status to: {status}")
            return {"status": "success", "message": f"Conversation status updated to {status} in test mode"}
            
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/status"
        payload = {"status": status}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to update conversation status: {str(e)}"}
    
    def assign_conversation(self, conversation_id: str, assignee_id: int):
        """Assign a conversation to a specific agent"""
        if self.test_mode:
            print(f"[TEST MODE] Assigning conversation {conversation_id} to agent {assignee_id}")
            return {"status": "success", "message": f"Conversation assigned to agent {assignee_id} in test mode"}
            
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/assignments"
        payload = {"assignee_id": assignee_id}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to assign conversation: {str(e)}"}
    
    def handle_sales_query(self, conversation_id: str, query: str, customer_id: str = None):
        """Handle a sales-related query using the ERPNext tool"""
        if self.test_mode:
            print(f"[TEST MODE] Handling sales query for conversation {conversation_id}: {query}")
            
            # Sample response for different types of sales queries
            if "plan" in query.lower() or "service" in query.lower():
                plans = erp_tool.get_service_plans()
                plan_info = "Here are our available plans:\n"
                for plan in plans.get("plans", [])[:3]:  # Limit to first 3 plans for brevity
                    plan_info += f"- {plan['name']}: {plan['speed_down']}Mbps down/{plan['speed_up']}Mbps up for ${plan['price']}/month\n"
                plan_info += "Would you like more details about any specific plan?"
                self.send_message(conversation_id, plan_info)
                
            elif "promo" in query.lower() or "discount" in query.lower() or "offer" in query.lower():
                promos = erp_tool.get_promotions()
                promo_info = "We have these special offers available:\n"
                for promo in promos.get("promotions", []):
                    promo_info += f"- {promo['name']}: {promo['description']}\n"
                self.send_message(conversation_id, promo_info)
                
            else:
                self.send_message(conversation_id, "I'd be happy to help you with your interest in our services. Are you looking for information about our internet plans, current promotions, or something else?")
                
            return {"status": "success", "message": "Sales query handled in test mode"}
        
        # In production mode, use the actual LangChain agent with ERPNext tools
        # This will be implemented in the main application
        
        return {"status": "pending", "message": "Sales query handling not implemented in production mode yet"}
    
    def handle_support_query(self, conversation_id: str, query: str, customer_id: str = None):
        """Handle a support-related query using the Splynx and UNMS tools"""
        if self.test_mode:
            print(f"[TEST MODE] Handling support query for conversation {conversation_id}: {query}")
            
            # Sample response for different types of support queries
            if "outage" in query.lower() or "down" in query.lower() or "not working" in query.lower():
                self.send_message(conversation_id, "I'm sorry to hear you're experiencing issues. Let me check the status of our network in your area. Can you please confirm your address or customer ID?")
                
            elif "bill" in query.lower() or "payment" in query.lower() or "invoice" in query.lower():
                if customer_id:
                    payment_info = splynx_tool.get_payment_history(customer_id)
                    self.send_message(conversation_id, f"I've checked your account. Your last payment of ${payment_info.get('last_payment_amount', 'N/A')} was received on {payment_info.get('last_payment_date', 'N/A')}. Your next bill of ${payment_info.get('next_invoice_amount', 'N/A')} is due on {payment_info.get('next_invoice_date', 'N/A')}.")
                else:
                    self.send_message(conversation_id, "I'd be happy to help you with your billing inquiry. Could you please provide your customer ID or the email address associated with your account?")
                
            elif "speed" in query.lower() or "slow" in query.lower():
                self.send_message(conversation_id, "I understand you're experiencing slow speeds. Let's troubleshoot this together. Have you tried restarting your router? Also, are you connected via WiFi or Ethernet cable?")
                
            else:
                self.send_message(conversation_id, "I'm here to help with your technical support needs. Could you please provide more details about the issue you're experiencing?")
                
            return {"status": "success", "message": "Support query handled in test mode"}
        
        # In production mode, use the actual LangChain agent with Splynx and UNMS tools
        # This will be implemented in the main application
        
        return {"status": "pending", "message": "Support query handling not implemented in production mode yet"}

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

chatwoot_handler = ChatwootHandler(
    api_key=os.getenv("CHATWOOT_API_KEY", "test_key"),
    account_id=os.getenv("CHATWOOT_ACCOUNT_ID", "1"),
    base_url=os.getenv("CHATWOOT_BASE_URL", "https://chatwoot.example.com")
)

# Define the tools available to the agent
tools = [
    Tool(
        name="get_customer_internet_status",
        func=splynx_tool.get_customer_internet_status,
        description="Get the current internet status for a customer by providing the customer ID"
    ),
    Tool(
        name="get_payment_history",
        func=splynx_tool.get_payment_history,
        description="Get payment history for a customer by providing the customer ID"
    ),
    Tool(
        name="get_order_status",
        func=erp_tool.get_order_status,
        description="Get the status of an order by providing the order ID"
    ),
    Tool(
        name="get_customer_info",
        func=erp_tool.get_customer_info,
        description="Get general information about a customer by providing the customer ID"
    ),
    Tool(
        name="get_device_status",
        func=unms_tool.get_device_status,
        description="Get the status of a network device by providing the device ID"
    ),
    Tool(
        name="get_outage_info",
        func=unms_tool.get_outage_info,
        description="Get information about current network outages by providing a location or area code"
    ),
    Tool(
        name="get_site_status",
        func=unms_tool.get_site_status,
        description="Get the status of a network site by providing the site ID"
    ),
    Tool(
        name="get_service_plans",
        func=erp_tool.get_service_plans,
        description="Get available service plans"
    ),
    Tool(
        name="get_promotions",
        func=erp_tool.get_promotions,
        description="Get current promotions"
    ),
    Tool(
        name="get_plan_details",
        func=erp_tool.get_plan_details,
        description="Get detailed information about a specific plan"
    )
]

# Import the agent prompt templates
from agent_prompts import get_system_prompt

# Create a dynamic agent that can adapt based on the conversation role
def create_agent_executor(role="support", context_data=None):
    """
    Create an agent executor with the appropriate prompt based on the detected role.
    
    Args:
        role: The detected role ("sales" or "support")
        context_data: Dictionary containing context information
        
    Returns:
        AgentExecutor instance
    """
    if context_data is None:
        context_data = {}
    
    # Get the appropriate system prompt based on the role
    system_prompt = get_system_prompt(role, context_data)
    
    # Create a memory buffer for the conversation
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create the agent executor
    if role == "sales":
        tools = [
            erp_tool_customer_info,
            erp_tool_service_plans,
            erp_tool_promotions,
            erp_tool_plan_details,
            erp_tool_order_status
        ]
    else:  # support role
        tools = [
            splynx_tool_internet_status,
            splynx_tool_payment_history,
            unms_tool_device_status,
            unms_tool_site_status,
            unms_tool_outage_info
        ]
    
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

# Default agent executor (will be replaced with dynamic creation in production)
agent_executor = create_agent_executor()

# Function to extract entity IDs from a message
def extract_entity_ids(message: str) -> Dict[str, str]:
    """Extract entity IDs from a message using regex patterns"""
    import re
    
    entity_patterns = {
        "customer_id": r"customer[_\s]?id[:\s]+([A-Z0-9]+)",
        "order_id": r"order[_\s]?id[:\s]+([A-Z0-9]+)",
        "device_id": r"device[_\s]?id[:\s]+([A-Z0-9]+)",
        "site_id": r"site[_\s]?id[:\s]+([A-Z0-9]+)",
        "plan_id": r"plan[_\s]?id[:\s]+([A-Z0-9\-]+)"
    }
    
    extracted_ids = {}
    
    for entity_type, pattern in entity_patterns.items():
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            extracted_ids[entity_type] = matches[0]
    
    return extracted_ids

# Function to process a message with the appropriate agent
def process_message(message: str, conversation_id: str, context_manager=None):
    """
    Process a message using the appropriate agent based on the conversation context.
    
    Args:
        message: The message to process
        conversation_id: The ID of the conversation
        context_manager: The conversation context manager
        
    Returns:
        The agent's response
    """
    # Default role and context data
    role = "support"
    context_data = {}
    
    # If we have a context manager, use it to determine the role and context
    if context_manager:
        # Get conversation history if available
        history = []
        if hasattr(chatwoot_handler, 'get_conversation_history'):
            history = chatwoot_handler.get_conversation_history(conversation_id)
        
        # Update the context with the new message
        context_data = context_manager.update_context(conversation_id, message, history)
        role = context_data.get("role", "support")
    
    # Extract entity IDs from the message
    entity_ids = extract_entity_ids(message)
    
    # Add extracted entity IDs to the context
    if context_manager and entity_ids:
        customer_info = context_data.get("customer_info", {})
        for entity_type, entity_id in entity_ids.items():
            if entity_type == "customer_id":
                customer_info["customer_id"] = entity_id
        
        # Update the context with the extracted customer ID
        if "customer_id" in entity_ids:
            context_manager.set_customer_info(conversation_id, {"customer_id": entity_ids["customer_id"]})
    
    # Create the appropriate agent based on the role and context
    agent = create_agent_executor(role, context_data)
    
    # Process the message with the agent
    response = agent.invoke({
        "input": message,
        "chat_history": []  # We could use actual chat history here if needed
    })
    
    return response["output"]

from flask import Flask, request, jsonify
app = Flask(__name__)

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

# ----- Main Application Entry Point -----

if __name__ == "__main__":
    # Load environment variables from .env file
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=debug)