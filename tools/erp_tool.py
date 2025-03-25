"""
ERPNext integration tool for retrieving business information.
"""
import os
import requests
from typing import Dict, List, Any

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("ERPNEXT_API_KEY") in [None, "", "your_erpnext_username"]
)

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
            return {
                "id": order_id,
                "status": "Processing",
                "created_at": "2025-03-20",
                "customer": "Test Customer",
                "items": [
                    {
                        "item_code": "FIBER-100",
                        "description": "Fiber 100Mbps Plan",
                        "qty": 1,
                        "rate": 89.99
                    }
                ],
                "delivery_date": "2025-03-27",
                "total": 89.99
            }
        
        try:
            endpoint = f"{self.base_url}/api/resource/Sales Order/{order_id}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Process and format the response
            order_data = data.get("data", {})
            return {
                "id": order_id,
                "status": order_data.get("status", "Unknown"),
                "created_at": order_data.get("creation", "Unknown"),
                "customer": order_data.get("customer_name", "Unknown"),
                "items": [
                    {
                        "item_code": item.get("item_code", "Unknown"),
                        "description": item.get("description", "Unknown"),
                        "qty": item.get("qty", 0),
                        "rate": item.get("rate", 0)
                    }
                    for item in order_data.get("items", [])
                ],
                "delivery_date": order_data.get("delivery_date", "Unknown"),
                "total": order_data.get("grand_total", 0)
            }
        except Exception as e:
            return {"error": f"Failed to retrieve order status: {str(e)}"}
    
    def get_customer_info(self, customer_id: str) -> Dict:
        """Get general information about a customer"""
        if self.test_mode:
            return {
                "id": customer_id,
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "123-456-7890",
                "address": "123 Test St, Test City, Test Country",
                "customer_type": "Individual",
                "territory": "United States",
                "customer_group": "Residential",
                "credit_limit": 1000.00,
                "status": "Active"
            }
        
        try:
            endpoint = f"{self.base_url}/api/resource/Customer/{customer_id}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Process and format the response
            customer_data = data.get("data", {})
            return {
                "id": customer_id,
                "name": customer_data.get("customer_name", "Unknown"),
                "email": customer_data.get("email_id", "Unknown"),
                "phone": customer_data.get("mobile_no", "Unknown"),
                "address": self._get_customer_address(customer_id),
                "customer_type": customer_data.get("customer_type", "Unknown"),
                "territory": customer_data.get("territory", "Unknown"),
                "customer_group": customer_data.get("customer_group", "Unknown"),
                "credit_limit": customer_data.get("credit_limit", 0),
                "status": "Active" if customer_data.get("disabled") == 0 else "Inactive"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve customer information: {str(e)}"}
    
    def _get_customer_address(self, customer_id: str) -> str:
        """Helper method to get a customer's address"""
        if self.test_mode:
            return "123 Test St, Test City, Test Country"
        
        try:
            endpoint = f"{self.base_url}/api/resource/Address?filters=[[\"Address\",\"customer\",\"=\",\"{customer_id}\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            addresses = data.get("data", [])
            if not addresses:
                return "No address found"
            
            # Get the first address
            address = addresses[0]
            return f"{address.get('address_line1', '')}, {address.get('city', '')}, {address.get('country', '')}"
        except Exception:
            return "Address unavailable"
    
    def get_service_plans(self, service_type: str = None) -> List[Dict]:
        """
        Get available service plans from ERPNext items
        
        Args:
            service_type: Optional filter for service type (e.g., "fiber", "dsl", "wireless")
            
        Returns:
            List of available service plans
        """
        if self.test_mode:
            plans = [
                {
                    "id": "FIBER-100",
                    "name": "Fiber 100Mbps",
                    "description": "100Mbps download / 50Mbps upload fiber internet",
                    "price": 89.99,
                    "setup_fee": 99.00,
                    "type": "fiber"
                },
                {
                    "id": "FIBER-500",
                    "name": "Fiber 500Mbps",
                    "description": "500Mbps download / 100Mbps upload fiber internet",
                    "price": 119.99,
                    "setup_fee": 99.00,
                    "type": "fiber"
                },
                {
                    "id": "FIBER-1000",
                    "name": "Fiber Gigabit",
                    "description": "1Gbps download / 200Mbps upload fiber internet",
                    "price": 149.99,
                    "setup_fee": 0.00,
                    "type": "fiber"
                },
                {
                    "id": "DSL-25",
                    "name": "DSL 25Mbps",
                    "description": "25Mbps download / 5Mbps upload DSL internet",
                    "price": 49.99,
                    "setup_fee": 49.00,
                    "type": "dsl"
                },
                {
                    "id": "WIRELESS-50",
                    "name": "Wireless 50Mbps",
                    "description": "50Mbps download / 10Mbps upload wireless internet",
                    "price": 69.99,
                    "setup_fee": 149.00,
                    "type": "wireless"
                }
            ]
            
            if service_type:
                plans = [plan for plan in plans if plan["type"] == service_type.lower()]
            
            return plans
        
        try:
            # Build filter for service type if provided
            filters = "[[\"Item\",\"item_group\",\"=\",\"Internet Plans\"]]"
            if service_type:
                filters = f"[[\"Item\",\"item_group\",\"=\",\"Internet Plans\"],[\"Item\",\"item_name\",\"like\",\"%{service_type}%\"]]"
            
            endpoint = f"{self.base_url}/api/resource/Item?filters={filters}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            plans = []
            for item in data.get("data", []):
                plan = {
                    "id": item.get("name"),
                    "name": item.get("item_name"),
                    "description": item.get("description", "No description available"),
                    "price": item.get("standard_rate", 0),
                    "setup_fee": self._get_setup_fee(item.get("name")),
                    "type": self._extract_service_type(item.get("item_name", ""))
                }
                plans.append(plan)
            
            return plans
        except Exception as e:
            return {"error": f"Failed to retrieve service plans: {str(e)}"}
    
    def _get_setup_fee(self, item_code: str) -> float:
        """Helper method to get setup fee for a service plan"""
        if self.test_mode:
            return 99.00
        
        try:
            endpoint = f"{self.base_url}/api/resource/Item Price?filters=[[\"Item Price\",\"item_code\",\"=\",\"{item_code}\"],[\"Item Price\",\"price_list\",\"=\",\"Setup Fee\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            prices = data.get("data", [])
            if not prices:
                return 0.00
            
            return prices[0].get("price_list_rate", 0.00)
        except Exception:
            return 0.00
    
    def _extract_service_type(self, item_name: str) -> str:
        """Helper method to extract service type from item name"""
        item_name = item_name.lower()
        if "fiber" in item_name:
            return "fiber"
        elif "dsl" in item_name:
            return "dsl"
        elif "wireless" in item_name:
            return "wireless"
        else:
            return "other"
    
    def get_promotions(self) -> List[Dict]:
        """
        Get current promotions from ERPNext pricing rules
        
        Returns:
            List of available promotions
        """
        if self.test_mode:
            return [
                {
                    "id": "PROMO-1",
                    "name": "New Customer Discount",
                    "description": "50% off first 3 months for new customers",
                    "discount_percentage": 50,
                    "discount_amount": 0,
                    "valid_from": "2025-01-01",
                    "valid_until": "2025-12-31",
                    "applicable_plans": ["FIBER-100", "FIBER-500", "FIBER-1000"]
                },
                {
                    "id": "PROMO-2",
                    "name": "Free Installation",
                    "description": "No setup fee for Fiber Gigabit plan",
                    "discount_percentage": 0,
                    "discount_amount": 99,
                    "valid_from": "2025-03-01",
                    "valid_until": "2025-04-30",
                    "applicable_plans": ["FIBER-1000"]
                },
                {
                    "id": "PROMO-3",
                    "name": "Bundle Discount",
                    "description": "10% off when bundling internet with TV service",
                    "discount_percentage": 10,
                    "discount_amount": 0,
                    "valid_from": "2025-01-01",
                    "valid_until": "2025-12-31",
                    "applicable_plans": ["FIBER-100", "FIBER-500", "FIBER-1000", "DSL-25", "WIRELESS-50"]
                }
            ]
        
        try:
            endpoint = f"{self.base_url}/api/resource/Pricing Rule?filters=[[\"Pricing Rule\",\"promotional_scheme_name\",\"!=\",\"\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Process and format the response
            rules = data.get("data", [])
            promotions = []
            
            for rule in rules:
                # Get applicable items for this promotion
                applicable_plans = self._get_applicable_items(rule.get("name", ""))
                
                promotions.append({
                    "id": rule.get("name", "Unknown"),
                    "name": rule.get("promotional_scheme_name", "Unknown"),
                    "description": rule.get("description", "No description available"),
                    "discount_percentage": rule.get("discount_percentage", 0),
                    "discount_amount": rule.get("discount_amount", 0),
                    "valid_from": rule.get("valid_from", "Unknown"),
                    "valid_until": rule.get("valid_upto", "Unknown"),
                    "applicable_plans": applicable_plans
                })
            
            return promotions
        except Exception as e:
            print(f"Error fetching promotions: {str(e)}")
            return []
    
    def _get_applicable_items(self, rule_id: str) -> List[str]:
        """Helper method to get applicable items for a promotion"""
        if self.test_mode:
            return ["FIBER-100", "FIBER-500", "FIBER-1000"]
        
        try:
            endpoint = f"{self.base_url}/api/resource/Pricing Rule Item?filters=[[\"Pricing Rule Item\",\"parent\",\"=\",\"{rule_id}\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return [item.get("item_code") for item in data.get("data", [])]
        except Exception:
            return []
    
    def get_plan_details(self, plan_id: str) -> Dict:
        """
        Get detailed information about a specific plan
        
        Args:
            plan_id: The ID of the plan to retrieve
            
        Returns:
            Dictionary containing plan details
        """
        if self.test_mode:
            test_plans = {
                "FIBER-100": {
                    "plan_id": "FIBER-100",
                    "name": "Fiber 100Mbps",
                    "description": "100Mbps download / 50Mbps upload fiber internet",
                    "price": 89.99,
                    "setup_fee": 99.00,
                    "type": "fiber",
                    "download_speed": "100 Mbps",
                    "upload_speed": "50 Mbps",
                    "data_cap": "Unlimited",
                    "contract_length": "12 months",
                    "early_termination_fee": 199.00,
                    "features": [
                        "Free Wi-Fi router",
                        "24/7 technical support",
                        "99.9% uptime guarantee"
                    ]
                },
                "FIBER-500": {
                    "plan_id": "FIBER-500",
                    "name": "Fiber 500Mbps",
                    "description": "500Mbps download / 100Mbps upload fiber internet",
                    "price": 119.99,
                    "setup_fee": 99.00,
                    "type": "fiber",
                    "download_speed": "500 Mbps",
                    "upload_speed": "100 Mbps",
                    "data_cap": "Unlimited",
                    "contract_length": "12 months",
                    "early_termination_fee": 199.00,
                    "features": [
                        "Free Wi-Fi router",
                        "24/7 technical support",
                        "99.9% uptime guarantee",
                        "Priority customer service"
                    ]
                },
                "FIBER-1000": {
                    "plan_id": "FIBER-1000",
                    "name": "Fiber Gigabit",
                    "description": "1Gbps download / 200Mbps upload fiber internet",
                    "price": 149.99,
                    "setup_fee": 0.00,
                    "type": "fiber",
                    "download_speed": "1000 Mbps",
                    "upload_speed": "200 Mbps",
                    "data_cap": "Unlimited",
                    "contract_length": "12 months",
                    "early_termination_fee": 199.00,
                    "features": [
                        "Free Wi-Fi router",
                        "24/7 technical support",
                        "99.9% uptime guarantee",
                        "Priority customer service",
                        "Free installation",
                        "Static IP address"
                    ]
                }
            }
            
            return test_plans.get(plan_id, {"error": "Plan not found"})
        
        try:
            endpoint = f"{self.base_url}/api/resource/Item/{plan_id}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            item_data = data.get("data", {})
            
            # Get additional details from item attributes
            attributes = self._get_item_attributes(plan_id)
            
            return {
                "plan_id": plan_id,
                "name": item_data.get("item_name", "Unknown"),
                "description": item_data.get("description", "No description available"),
                "price": item_data.get("standard_rate", 0),
                "setup_fee": self._get_setup_fee(plan_id),
                "type": self._extract_service_type(item_data.get("item_name", "")),
                "download_speed": attributes.get("download_speed", "Unknown"),
                "upload_speed": attributes.get("upload_speed", "Unknown"),
                "data_cap": attributes.get("data_cap", "Unknown"),
                "contract_length": attributes.get("contract_length", "Unknown"),
                "early_termination_fee": float(attributes.get("early_termination_fee", 0)),
                "features": self._get_item_features(plan_id)
            }
        except Exception as e:
            return {"error": f"Failed to retrieve plan details: {str(e)}"}
    
    def _get_item_attributes(self, item_code: str) -> Dict:
        """Helper method to get attributes for an item"""
        if self.test_mode:
            return {
                "download_speed": "100 Mbps",
                "upload_speed": "50 Mbps",
                "data_cap": "Unlimited",
                "contract_length": "12 months",
                "early_termination_fee": "199.00"
            }
        
        try:
            endpoint = f"{self.base_url}/api/resource/Item Attribute Value?filters=[[\"Item Attribute Value\",\"parent\",\"=\",\"{item_code}\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            attributes = {}
            for attr in data.get("data", []):
                attributes[attr.get("attribute")] = attr.get("attribute_value")
            
            return attributes
        except Exception:
            return {}
    
    def _get_item_features(self, item_code: str) -> List[str]:
        """Helper method to get features for an item"""
        if self.test_mode:
            return [
                "Free Wi-Fi router",
                "24/7 technical support",
                "99.9% uptime guarantee"
            ]
        
        try:
            endpoint = f"{self.base_url}/api/resource/Item Feature?filters=[[\"Item Feature\",\"parent\",\"=\",\"{item_code}\"]]"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return [feature.get("description") for feature in data.get("data", [])]
        except Exception:
            return []
