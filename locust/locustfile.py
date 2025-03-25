import json
import random
from locust import HttpUser, task, between

# Sample customer and order IDs for testing
CUSTOMER_IDS = ["CUS-12345", "CUS-23456", "CUS-34567", "CUS-45678", "CUS-56789"]
ORDER_IDS = ["ORD-12345", "ORD-23456", "ORD-34567", "ORD-45678", "ORD-56789"]

# Sample sales and support queries
SALES_QUERIES = [
    "I'm interested in your fiber internet plans",
    "What are your current promotions?",
    "Can you tell me about your business internet packages?",
    "Do you offer any bundle deals?",
    "I want to upgrade my current plan"
]

SUPPORT_QUERIES = [
    "My internet is slow",
    "I'm having trouble connecting to WiFi",
    "When will my service be installed?",
    "I need to reset my password",
    "My bill seems incorrect"
]

# Add customer and order IDs to some queries
CUSTOMER_QUERIES = [
    "Can you check my account status? My customer ID is {}",
    "I need help with my account {}",
    "What's the status of my service? Customer ID: {}"
]

ORDER_QUERIES = [
    "What's the status of my order {}?",
    "I placed an order with ID {} and need an update",
    "Order {} hasn't been delivered yet"
]

class ChatwootUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1-5 seconds between tasks
    
    def on_start(self):
        # Initialize conversation IDs for each user
        self.sales_conversation_id = f"sales-convo-{random.randint(1000, 9999)}"
        self.support_conversation_id = f"support-convo-{random.randint(1000, 9999)}"
    
    @task(3)  # Higher weight for sales queries
    def send_sales_query(self):
        # Randomly select a sales query
        if random.random() < 0.3:  # 30% chance to include customer ID
            customer_id = random.choice(CUSTOMER_IDS)
            query = random.choice(CUSTOMER_QUERIES).format(customer_id)
        else:
            query = random.choice(SALES_QUERIES)
        
        # Send the query to the sales endpoint
        payload = {
            "message": query,
            "conversation_id": self.sales_conversation_id,
            "role": "sales"
        }
        
        self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    
    @task(2)  # Lower weight for support queries
    def send_support_query(self):
        # Randomly select a support query
        if random.random() < 0.2:  # 20% chance to include order ID
            order_id = random.choice(ORDER_IDS)
            query = random.choice(ORDER_QUERIES).format(order_id)
        else:
            query = random.choice(SUPPORT_QUERIES)
        
        # Send the query to the support endpoint
        payload = {
            "message": query,
            "conversation_id": self.support_conversation_id,
            "role": "support"
        }
        
        self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    
    @task(1)  # Lowest weight for checking conversation context
    def get_conversation_context(self):
        # Randomly choose between sales and support conversation
        conversation_id = random.choice([self.sales_conversation_id, self.support_conversation_id])
        
        # Get the conversation context
        self.client.get(f"/api/conversation_context/{conversation_id}")
