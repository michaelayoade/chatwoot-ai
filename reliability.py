"""
Simplified reliability wrapper implementation for testing the Chatwoot webhook functionality.
"""
from logger_config import logger, llm_metrics

class APIReliabilityWrapper:
    """Wrapper for API calls with circuit breaker and rate limiting"""
    
    def __init__(self, api_name, circuit=None, rate_limiter=None, metrics_enabled=False):
        self.api_name = api_name
        self.circuit = circuit
        self.rate_limiter = rate_limiter
        self.metrics_enabled = metrics_enabled
        
    def call(self, func, *args, **kwargs):
        """Call the API function with reliability features"""
        logger.info(f"calling_api", api_name=self.api_name)
        
        # Check circuit breaker state
        if self.circuit and self.circuit.state == "open":
            logger.warning(f"circuit_open", api_name=self.api_name)
            return {"error": f"Circuit is open for {self.api_name} API"}
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Record success
            if self.circuit:
                self.circuit.state = "closed"
                
            return result
        except Exception as e:
            # Record failure
            if self.circuit:
                self.circuit.state = "open"
                
            logger.error(f"api_call_failed", api_name=self.api_name, error=str(e))
            raise

class LLMReliabilityWrapper:
    """Wrapper for LLM calls with metrics tracking and error handling"""
    
    def __init__(self, model, metrics=llm_metrics, cache_enabled=False, metrics_enabled=True, fallback_response=None):
        self.model_name = model  # Store as model_name for backward compatibility
        self.metrics = metrics
        self.cache_enabled = cache_enabled
        self.metrics_enabled = metrics_enabled
        self.fallback_response = fallback_response or "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment."
        
    def generate(self, func, *args, **kwargs):
        """Call the LLM function with reliability features"""
        # Track metrics only if enabled
        if self.metrics_enabled:
            @self.metrics.track
            def tracked_func(*args, **kwargs):
                return func(*args, **kwargs)
        else:
            tracked_func = func
        
        try:
            # Call the function with tracking
            return tracked_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"llm_call_failed", model=self.model_name, error=str(e))
            # Return the fallback response
            return self.fallback_response
