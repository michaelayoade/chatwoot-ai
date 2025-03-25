"""
Simplified rate limiter implementation for testing the Chatwoot webhook functionality.
"""
class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, name, max_calls=10, time_period=60):
        self.name = name
        self.max_calls = max_calls
        self.time_period = time_period
        
    def __str__(self):
        return f"RateLimiter({self.name}, max_calls={self.max_calls}, time_period={self.time_period}s)"

# Create rate limiter instances
erp_rate_limiter = RateLimiter("erp")
splynx_rate_limiter = RateLimiter("splynx")
unms_rate_limiter = RateLimiter("unms")
