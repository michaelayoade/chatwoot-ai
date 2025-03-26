"""
Simplified test script for reliability features.
This script tests the circuit breaker and rate limiting functionality.
"""
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set test mode to True to avoid making actual API calls
os.environ["TEST_MODE"] = "true"

# Import after setting TEST_MODE
from api_circuit_breaker import CircuitBreaker
from rate_limiter import RateLimiter
from handlers.chatwoot_handler import ChatwootHandler
from logger_config import logger

def test_circuit_breaker():
    """Test the circuit breaker functionality"""
    print("\nTesting circuit breaker functionality...")
    
    # Create a circuit breaker
    circuit_breaker = CircuitBreaker("test_circuit")
    circuit_breaker.state = "closed"
    
    # Test state changes
    print("Testing circuit breaker states...")
    print(f"Initial state: {circuit_breaker.state}")
    
    # Simulate opening the circuit
    circuit_breaker.state = "open"
    print(f"After failure: {circuit_breaker.state}")
    
    # Simulate half-open state
    circuit_breaker.state = "half-open"
    print(f"After timeout: {circuit_breaker.state}")
    
    # Simulate closing the circuit again
    circuit_breaker.state = "closed"
    print(f"After recovery: {circuit_breaker.state}")
    
    return circuit_breaker

def test_rate_limiter():
    """Test the rate limiter functionality"""
    print("\nTesting rate limiter functionality...")
    
    # Create a rate limiter
    rate_limiter = RateLimiter("test_rate_limiter")
    
    # Print rate limiter info
    print(f"Rate limiter: {rate_limiter}")
    
    return rate_limiter

def test_chatwoot_handler_reliability():
    """Test the reliability features in the Chatwoot handler"""
    print("\nTesting Chatwoot handler reliability features...")
    
    # Create a Chatwoot handler
    chatwoot_handler = ChatwootHandler(
        api_key=os.getenv("CHATWOOT_API_KEY", "test_key"),
        account_id=os.getenv("CHATWOOT_ACCOUNT_ID", "1"),
        base_url=os.getenv("CHATWOOT_BASE_URL", "https://chatwoot.example.com")
    )
    
    # Test sending multiple messages in quick succession
    print("Sending multiple messages in quick succession...")
    conversation_id = "789"
    
    for i in range(5):
        message = f"Test message {i+1} for reliability testing"
        result = chatwoot_handler.send_message(conversation_id, message)
        print(f"Message {i+1} result: {json.dumps(result, indent=2)}")
    
    return chatwoot_handler

if __name__ == "__main__":
    # Run the tests
    test_circuit_breaker()
    test_rate_limiter()
    test_chatwoot_handler_reliability()
