import json
import random
import time
from locust import HttpUser, task, between, events, constant_pacing

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

# Queries for testing semantic caching (similar queries with slight variations)
SEMANTIC_CACHE_QUERIES = [
    "What internet plans do you offer?",
    "Tell me about your internet packages",
    "What internet options are available?",
    "I want to know about internet plans",
    "Show me your internet offerings"
]

# Queries for testing circuit breaker (queries that might trigger external API calls)
EXTERNAL_API_QUERIES = [
    "Check my bill for customer {}",
    "What's my current balance for account {}?",
    "When is my next payment due for customer ID {}?",
    "Show me my usage statistics for account {}",
    "What's my current plan details for customer ID {}?"
]

# Metrics for tracking test results
metrics = {
    "cache_hits": 0,
    "cache_misses": 0,
    "circuit_breaker_open": 0,
    "rate_limited_requests": 0
}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting load test for LangChain-Chatwoot reliability components")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n=== Test Results ===")
    print(f"Cache Hits: {metrics['cache_hits']}")
    print(f"Cache Misses: {metrics['cache_misses']}")
    print(f"Circuit Breaker Open Events: {metrics['circuit_breaker_open']}")
    print(f"Rate Limited Requests: {metrics['rate_limited_requests']}")

class ChatwootUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1-5 seconds between tasks
    
    def on_start(self):
        # Initialize conversation IDs for each user
        self.sales_conversation_id = f"sales-convo-{random.randint(1000, 9999)}"
        self.support_conversation_id = f"support-convo-{random.randint(1000, 9999)}"
        self.cache_conversation_id = f"cache-convo-{random.randint(1000, 9999)}"
        self.api_conversation_id = f"api-convo-{random.randint(1000, 9999)}"
        self.burst_conversation_id = f"burst-convo-{random.randint(1000, 9999)}"
    
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
        
        response = self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="Regular Sales Query"
        )
        
        self._check_response_for_reliability_headers(response)
    
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
        
        response = self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="Regular Support Query"
        )
        
        self._check_response_for_reliability_headers(response)
    
    @task(1)  # Lowest weight for checking conversation context
    def get_conversation_context(self):
        # Randomly choose between sales and support conversation
        conversation_id = random.choice([self.sales_conversation_id, self.support_conversation_id])
        
        # Get the conversation context
        response = self.client.get(
            f"/api/conversation_context/{conversation_id}",
            name="Get Conversation Context"
        )
        
        self._check_response_for_reliability_headers(response)
    
    @task(2)  # Test semantic caching with similar queries
    def test_semantic_cache(self):
        # Send semantically similar queries in sequence to test cache
        query = random.choice(SEMANTIC_CACHE_QUERIES)
        
        payload = {
            "message": query,
            "conversation_id": self.cache_conversation_id,
            "role": "sales"
        }
        
        response = self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="Semantic Cache Query"
        )
        
        self._check_response_for_reliability_headers(response)
        
        # Check if response was cached
        if response.headers.get("X-Cache-Hit") == "true":
            metrics["cache_hits"] += 1
        else:
            metrics["cache_misses"] += 1
    
    @task(1)  # Test circuit breaker with API-intensive queries
    def test_circuit_breaker(self):
        # Send queries that might trigger external API calls
        customer_id = random.choice(CUSTOMER_IDS)
        query = random.choice(EXTERNAL_API_QUERIES).format(customer_id)
        
        payload = {
            "message": query,
            "conversation_id": self.api_conversation_id,
            "role": "support"
        }
        
        response = self.client.post(
            "/api/process_message",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="External API Query"
        )
        
        self._check_response_for_reliability_headers(response)
        
        # Check if circuit breaker was triggered
        if response.headers.get("X-Circuit-Open") == "true":
            metrics["circuit_breaker_open"] += 1
    
    @task(1)  # Test rate limiting with burst requests
    def test_rate_limiting(self):
        # Send a burst of requests to trigger rate limiting
        for _ in range(5):  # Send 5 requests in quick succession
            query = f"Quick question {random.randint(1, 1000)}: {random.choice(SALES_QUERIES)}"
            
            payload = {
                "message": query,
                "conversation_id": self.burst_conversation_id,
                "role": "sales"
            }
            
            response = self.client.post(
                "/api/process_message",
                json=payload,
                headers={"Content-Type": "application/json"},
                name="Burst Query",
                catch_response=True
            )
            
            # Check if rate limiting was applied
            if response.status_code == 429 or response.headers.get("X-Rate-Limited") == "true":
                metrics["rate_limited_requests"] += 1
                response.success()  # Mark as success since we're testing rate limiting
            
            self._check_response_for_reliability_headers(response)
            
            # Don't wait between burst requests
            time.sleep(0.1)
    
    def _check_response_for_reliability_headers(self, response):
        """Check response headers for reliability component information"""
        try:
            # Log reliability headers if present
            headers_to_check = [
                "X-Cache-Hit", 
                "X-Circuit-Open", 
                "X-Rate-Limited",
                "X-Response-Time",
                "X-API-Calls"
            ]
            
            for header in headers_to_check:
                if header in response.headers:
                    self.environment.events.request.fire(
                        request_type="reliability",
                        name=f"Header: {header}",
                        response_time=0,
                        response_length=0,
                        exception=None,
                        context={header: response.headers.get(header)}
                    )
        except Exception as e:
            print(f"Error checking reliability headers: {e}")

class BurstUser(HttpUser):
    """User class for simulating traffic bursts to test rate limiting"""
    wait_time = constant_pacing(10)  # One burst every 10 seconds
    
    def on_start(self):
        self.burst_conversation_id = f"heavy-burst-{random.randint(1000, 9999)}"
    
    @task
    def heavy_burst(self):
        # Send a heavy burst of 10 requests in very quick succession
        for i in range(10):
            query = f"Burst query {i}: {random.choice(SALES_QUERIES)}"
            
            payload = {
                "message": query,
                "conversation_id": self.burst_conversation_id,
                "role": "sales"
            }
            
            with self.client.post(
                "/api/process_message",
                json=payload,
                headers={"Content-Type": "application/json"},
                name="Heavy Burst Query",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    metrics["rate_limited_requests"] += 1
                    response.success()  # Mark as success since we're testing rate limiting
            
            # Almost no delay between requests in a burst
            time.sleep(0.05)
