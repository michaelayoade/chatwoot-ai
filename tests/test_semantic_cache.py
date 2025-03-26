"""
Test suite for the semantic cache used by the agent classes.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import json
import time
import hashlib

# Set up test environment
os.environ["TEST_MODE"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

# Import the semantic cache
from semantic_cache import semantic_cache

class TestSemanticCache(unittest.TestCase):
    """Test case for the semantic cache."""
    
    def setUp(self):
        """Set up the test case."""
        # Clear the cache before each test
        self._clear_cache()
        
        # Create test data
        self.test_key = "test:message:hash123"
        self.test_value = {
            "response": "This is a test response",
            "timestamp": time.time(),
            "role": "sales"
        }
    
    def _clear_cache(self):
        """Clear the semantic cache."""
        semantic_cache.clear()
    
    def test_set_and_get(self):
        """Test setting and getting values from the cache."""
        # Set a value in the cache
        semantic_cache.set(self.test_key, self.test_value)
        
        # Get the value from the cache
        cached_value = semantic_cache.get(self.test_key)
        self.assertIsNotNone(cached_value)
        self.assertEqual(cached_value["response"], self.test_value["response"])
        self.assertEqual(cached_value["role"], self.test_value["role"])
    
    def test_missing_key(self):
        """Test checking if a key is missing in the cache."""
        # Key should not exist initially
        self.assertIsNone(semantic_cache.get(self.test_key))
        
        # Set a value
        semantic_cache.set(self.test_key, self.test_value)
        
        # Key should exist now
        self.assertIsNotNone(semantic_cache.get(self.test_key))
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key from the cache."""
        # Get a nonexistent key
        cached_value = semantic_cache.get("nonexistent:key")
        self.assertIsNone(cached_value)
    
    def test_cache_key_generation(self):
        """Test the generation of cache keys."""
        # Create a message and context
        message = "What internet plans do you offer?"
        context_data = {
            "role": "sales",
            "conversation_id": "conv123"
        }
        
        # Generate a cache key
        # This is a simplified version of what the agent classes do
        role = context_data.get("role", "unknown")
        
        # Create a hash of the context data
        context_hash = hashlib.sha256(
            json.dumps(context_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Create the cache key
        cache_key = f"{role}:{message}:{context_hash}"
        
        # Check that the key has the expected format
        self.assertTrue(cache_key.startswith(f"{role}:{message}:"))
        
        # Set a value with this key
        semantic_cache.set(cache_key, self.test_value)
        
        # Check that we can retrieve it
        cached_value = semantic_cache.get(cache_key)
        self.assertIsNotNone(cached_value)
        self.assertEqual(cached_value["response"], self.test_value["response"])
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        # Create a cache with a very short TTL for testing
        from semantic_cache import SemanticCache
        test_cache = SemanticCache("test_cache", ttl=0.1)  # 100ms TTL
        
        # Set a value
        test_cache.set(self.test_key, self.test_value)
        
        # Value should exist immediately
        self.assertIsNotNone(test_cache.get(self.test_key))
        
        # Wait for the TTL to expire
        time.sleep(0.2)  # 200ms
        
        # Value should be gone now
        self.assertIsNone(test_cache.get(self.test_key))
    
    def test_cache_update(self):
        """Test updating a value in the cache."""
        # Set an initial value
        semantic_cache.set(self.test_key, self.test_value)
        
        # Update the value
        updated_value = {
            "response": "This is an updated response",
            "timestamp": time.time(),
            "role": "sales"
        }
        semantic_cache.set(self.test_key, updated_value)
        
        # Get the updated value
        cached_value = semantic_cache.get(self.test_key)
        self.assertIsNotNone(cached_value)
        self.assertEqual(cached_value["response"], updated_value["response"])
    
    def test_cache_with_different_roles(self):
        """Test caching with different roles."""
        # Create keys for different roles
        sales_key = "sales:message:hash123"
        support_key = "support:message:hash123"
        
        # Set values for each role
        sales_value = {
            "response": "This is a sales response",
            "timestamp": time.time(),
            "role": "sales"
        }
        support_value = {
            "response": "This is a support response",
            "timestamp": time.time(),
            "role": "support"
        }
        
        semantic_cache.set(sales_key, sales_value)
        semantic_cache.set(support_key, support_value)
        
        # Get the values
        cached_sales = semantic_cache.get(sales_key)
        cached_support = semantic_cache.get(support_key)
        
        # Check that the values are correct
        self.assertEqual(cached_sales["response"], sales_value["response"])
        self.assertEqual(cached_support["response"], support_value["response"])
        
        # Check that the roles are preserved
        self.assertEqual(cached_sales["role"], "sales")
        self.assertEqual(cached_support["role"], "support")
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        # Set some values
        semantic_cache.set(self.test_key, self.test_value)
        semantic_cache.set("another:key", {"response": "Another response"})
        
        # Clear the cache
        semantic_cache.clear()
        
        # Check that the values are gone
        self.assertIsNone(semantic_cache.get(self.test_key))
        self.assertIsNone(semantic_cache.get("another:key"))

if __name__ == "__main__":
    unittest.main()
