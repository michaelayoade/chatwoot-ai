"""
Simplified semantic cache implementation for testing the Chatwoot webhook functionality.
"""
import time
from logger_config import logger

class SemanticCache:
    """Simple semantic cache implementation"""
    
    def __init__(self, name, ttl=3600):
        self.name = name
        self.ttl = ttl  # Time to live in seconds
        self.cache = {}
        
    def get(self, key):
        """Get a value from the cache"""
        if key not in self.cache:
            logger.info("cache_miss", cache=self.name, key=key)
            return None
        
        # Check if the entry has expired
        entry = self.cache[key]
        if time.time() > entry["expiry"]:
            logger.info("cache_expired", cache=self.name, key=key)
            del self.cache[key]
            return None
        
        logger.info("cache_hit", cache=self.name, key=key)
        return entry["value"]
    
    def set(self, key, value):
        """Set a value in the cache"""
        self.cache[key] = {
            "value": value,
            "expiry": time.time() + self.ttl
        }
        logger.info("cache_set", cache=self.name, key=key)
        
    def clear(self):
        """Clear the cache"""
        self.cache = {}
        logger.info("cache_cleared", cache=self.name)

# Create a semantic cache instance
llm_cache = SemanticCache("llm_responses")

# Export the semantic_cache variable for import by other modules
semantic_cache = SemanticCache("semantic_responses")
