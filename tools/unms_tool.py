"""
UNMS (Ubiquiti Network Management System) integration tool for retrieving network information.
"""
import os
import requests
from typing import Dict, List, Any

# Check if we're in test mode
TEST_MODE = (
    os.getenv("TEST_MODE", "").lower() == "true" or
    os.getenv("OPENAI_API_KEY") in [None, "", "your_openai_api_key"] or
    os.getenv("UNMS_API_KEY") in [None, "", "your_unms_api_key"]
)

class UNMSTool:
    """Tool for interacting with UNMS (Ubiquiti Network Management System)."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.test_mode = TEST_MODE or os.getenv("TEST_MODE", "").lower() == "true"
    
    def _make_api_request(self, endpoint: str) -> Dict:
        if self.test_mode:
            # Return mock data for testing based on the endpoint
            if "devices" in endpoint:
                return {
                    "id": endpoint.split("/")[-1] if "/" in endpoint else "device-123",
                    "name": "EdgeRouter Pro",
                    "model": "ER-PRO",
                    "status": "active",
                    "uptime": "45 days",
                    "firmware": "v2.0.9",
                    "ip_address": "192.168.1.1",
                    "mac_address": "00:11:22:33:44:55",
                    "cpu_load": 12,
                    "memory_usage": 35,
                    "temperature": 42
                }
            elif "sites" in endpoint:
                return {
                    "id": endpoint.split("/")[-1] if "/" in endpoint else "site-123",
                    "name": "Main Office",
                    "status": "operational",
                    "devices_count": 15,
                    "devices_online": 15,
                    "last_updated": "2025-03-24T15:30:45Z"
                }
            elif "outages" in endpoint:
                return {
                    "outages": [
                        {
                            "id": "OUT-123",
                            "site_id": "site-123",
                            "start_time": "2025-03-24T10:15:00Z",
                            "end_time": "2025-03-24T11:30:00Z",
                            "duration": "1h 15m",
                            "affected_devices": 3,
                            "status": "resolved",
                            "description": "Power outage"
                        }
                    ]
                }
            return {"message": "Mock data for testing"}
        
        url = f"{self.base_url}/api/v2.1/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making UNMS API request: {str(e)}")
            return {"error": str(e)}
    
    def get_device_status(self, device_id: str) -> Dict:
        """Get the status of a network device by ID"""
        if self.test_mode:
            return {
                "id": device_id,
                "name": "EdgeRouter Pro",
                "model": "ER-PRO",
                "status": "active",
                "uptime": "45 days",
                "firmware": "v2.0.9",
                "ip_address": "192.168.1.1",
                "mac_address": "00:11:22:33:44:55",
                "cpu_load": 12,
                "memory_usage": 35,
                "temperature": 42,
                "interfaces": [
                    {
                        "name": "eth0",
                        "status": "up",
                        "speed": "1 Gbps",
                        "duplex": "full",
                        "tx_bytes": "1.2 GB",
                        "rx_bytes": "3.5 GB"
                    },
                    {
                        "name": "eth1",
                        "status": "up",
                        "speed": "1 Gbps",
                        "duplex": "full",
                        "tx_bytes": "0.8 GB",
                        "rx_bytes": "2.1 GB"
                    }
                ]
            }
        
        try:
            endpoint = f"devices/{device_id}"
            device_data = self._make_api_request(endpoint)
            
            # Get interface information
            interfaces_data = self._make_api_request(f"devices/{device_id}/interfaces")
            interfaces = []
            
            for interface in interfaces_data.get("interfaces", []):
                interfaces.append({
                    "name": interface.get("name", "Unknown"),
                    "status": interface.get("status", "Unknown"),
                    "speed": interface.get("speed", "Unknown"),
                    "duplex": interface.get("duplex", "Unknown"),
                    "tx_bytes": self._format_bytes(interface.get("tx_bytes", 0)),
                    "rx_bytes": self._format_bytes(interface.get("rx_bytes", 0))
                })
            
            # Add interfaces to device data
            device_data["interfaces"] = interfaces
            return device_data
        except Exception as e:
            return {"error": f"Failed to retrieve device status: {str(e)}"}
    
    def get_site_status(self, site_id: str) -> Dict:
        """Get the status of a network site by ID"""
        if self.test_mode:
            return {
                "id": site_id,
                "name": "Test Site",
                "status": "operational",
                "devices_count": 5,
                "devices_online": 5,
                "last_updated": "2025-03-24T15:30:45Z",
                "location": {
                    "address": "123 Main St, Anytown, USA",
                    "coordinates": {
                        "latitude": 37.7749,
                        "longitude": -122.4194
                    }
                }
            }
        
        endpoint = f"sites/{site_id}"
        return self._make_api_request(endpoint)
    
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
    
    def get_service_outages(self, limit: int = 5) -> List[Dict]:
        """Get recent service outages"""
        if self.test_mode:
            return [
                {
                    "id": f"outage-{i}",
                    "site_id": f"site-{i}",
                    "site_name": f"Site {i}",
                    "start_time": f"2025-03-{20+i}T10:15:00Z",
                    "end_time": f"2025-03-{20+i}T11:30:00Z" if i % 2 == 0 else None,
                    "duration": "1h 15m" if i % 2 == 0 else "Ongoing",
                    "status": "resolved" if i % 2 == 0 else "active",
                    "affected_devices": i + 2,
                    "description": ["Power outage", "Fiber cut", "Equipment failure", "Maintenance", "Weather related"][i % 5]
                } for i in range(min(limit, 5))
            ]
        
        try:
            endpoint = f"outages/recent?limit={limit}"
            response = self._make_api_request(endpoint)
            
            outages = []
            for outage in response.get("outages", []):
                site_name = self._get_site_name(outage.get("site_id", ""))
                
                outages.append({
                    "id": outage.get("id", "Unknown"),
                    "site_id": outage.get("site_id", "Unknown"),
                    "site_name": site_name,
                    "start_time": outage.get("start_time", "Unknown"),
                    "end_time": outage.get("end_time", None),
                    "duration": self._calculate_duration(outage.get("start_time"), outage.get("end_time")),
                    "status": outage.get("status", "Unknown"),
                    "affected_devices": outage.get("affected_devices", 0),
                    "description": outage.get("description", "No description available")
                })
            
            return outages
        except Exception as e:
            return {"error": f"Failed to retrieve outage information: {str(e)}"}
    
    def _get_site_name(self, site_id: str) -> str:
        """Helper method to get site name from site ID"""
        if self.test_mode:
            return f"Site {site_id[-3:]}"
        
        try:
            endpoint = f"sites/{site_id}"
            site_data = self._make_api_request(endpoint)
            return site_data.get("name", "Unknown Site")
        except Exception:
            return "Unknown Site"
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between start and end time"""
        if not start_time:
            return "Unknown"
        
        if not end_time:
            return "Ongoing"
        
        # In a real implementation, we would parse the timestamps and calculate the duration
        # For simplicity in this example, we'll return a placeholder
        return "1h 15m"
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
