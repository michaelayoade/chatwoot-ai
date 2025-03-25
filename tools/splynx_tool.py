"""
Splynx integration tool for retrieving internet service information.
"""
import os
import requests
from typing import Dict, List, Any

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("SPLYNX_API_KEY") in [None, "", "your_splynx_api_key"]
)

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
        if self.test_mode:
            return {
                "customer_id": customer_id,
                "status": "Active",
                "plan": "Fiber 100Mbps",
                "ip_address": "192.168.1.100",
                "last_online": "2025-03-24T15:30:45Z",
                "signal_strength": "Excellent",
                "download_speed": "95.2 Mbps",
                "upload_speed": "48.7 Mbps",
                "data_used": "256.7 GB",
                "data_limit": "Unlimited",
                "usage": {
                    "current": "256.7 GB",
                    "limit": "Unlimited",
                    "percentage": 60
                }
            }
        
        try:
            endpoint = f"customers/{customer_id}/internet/services"
            response = self._make_api_request(endpoint)
            
            # Process and format the response
            service = response.get("service", {})
            data_used = service.get("data_used", 0)
            data_limit = service.get("data_limit", "Unlimited")
            
            # Calculate usage percentage if limit is not unlimited
            usage_percentage = 0
            if data_limit != "Unlimited" and data_limit > 0:
                usage_percentage = min(int((data_used / data_limit) * 100), 100)
            
            return {
                "customer_id": customer_id,
                "status": service.get("status", "Unknown"),
                "plan": service.get("tariff_name", "Unknown"),
                "ip_address": service.get("ip", "Unknown"),
                "last_online": service.get("last_online", "Unknown"),
                "signal_strength": self._calculate_signal_strength(service.get("signal", 0)),
                "download_speed": f"{service.get('download', 0)} Mbps",
                "upload_speed": f"{service.get('upload', 0)} Mbps",
                "data_used": f"{data_used} GB",
                "data_limit": data_limit,
                "usage": {
                    "current": f"{data_used} GB",
                    "limit": data_limit,
                    "percentage": usage_percentage
                }
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
    
    def _calculate_signal_strength(self, signal_value: float) -> str:
        """Calculate signal strength category based on signal value"""
        if signal_value >= -50:
            return "Excellent"
        elif signal_value >= -60:
            return "Good"
        elif signal_value >= -70:
            return "Fair"
        else:
            return "Poor"
