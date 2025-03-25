"""
Simplified logger configuration for testing the Chatwoot webhook functionality.
"""
import logging
import time
import json
from functools import wraps

# Configure a basic logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a logger instance
base_logger = logging.getLogger('langchain-chatwoot')

# Create a wrapper for structured logging
class StructuredLogger:
    """Wrapper for structured logging"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def _format_message(self, message, **kwargs):
        """Format a message with keyword arguments"""
        if kwargs:
            return f"{message} {json.dumps(kwargs)}"
        return message
    
    def info(self, message, **kwargs):
        """Log an info message with structured data"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message, **kwargs):
        """Log a warning message with structured data"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message, **kwargs):
        """Log an error message with structured data"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def debug(self, message, **kwargs):
        """Log a debug message with structured data"""
        self.logger.debug(self._format_message(message, **kwargs))

# Create a structured logger instance
logger = StructuredLogger(base_logger)

# Simple metrics tracking for LLM calls
class LLMMetrics:
    """Simple metrics tracking for LLM calls"""
    
    def __init__(self):
        self.total_tokens = 0
        self.total_calls = 0
        self.total_cost = 0
    
    def track(self, func):
        """Decorator to track LLM metrics"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Call the original function
            result = func(*args, **kwargs)
            
            # Update metrics
            self.total_calls += 1
            
            # Log the call
            duration = time.time() - start_time
            logger.info(
                "llm_call",
                duration_seconds=duration,
                total_calls=self.total_calls
            )
            
            return result
        
        return wrapper

# Create an instance of LLMMetrics
llm_metrics = LLMMetrics()
