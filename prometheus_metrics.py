"""
Simplified Prometheus metrics implementation for testing the Chatwoot webhook functionality.
"""
from functools import wraps
import time
from logger_config import logger

def track_conversation(func):
    """Decorator to track conversation metrics"""
    @wraps(func)
    def wrapper(message, conversation_id, *args, **kwargs):
        start_time = time.time()
        
        try:
            # Call the original function
            result = func(message, conversation_id, *args, **kwargs)
            
            # Record success metrics
            duration = time.time() - start_time
            logger.info(
                "conversation_processed",
                conversation_id=conversation_id,
                duration_seconds=duration,
                status="success"
            )
            
            return result
        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            logger.error(
                "conversation_failed",
                conversation_id=conversation_id,
                duration_seconds=duration,
                status="error",
                error=str(e)
            )
            raise
    
    return wrapper

def track_request(func=None, endpoint_name=None):
    """Decorator to track API request metrics"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or f.__name__
            
            try:
                # Call the original function
                result = f(*args, **kwargs)
                
                # Record success metrics
                duration = time.time() - start_time
                logger.info(
                    "api_request",
                    endpoint=endpoint,
                    duration_seconds=duration,
                    status="success"
                )
                
                return result
            except Exception as e:
                # Record failure metrics
                duration = time.time() - start_time
                logger.error(
                    "api_request_failed",
                    endpoint=endpoint,
                    duration_seconds=duration,
                    status="error",
                    error=str(e)
                )
                raise
        
        return wrapper
    
    # Handle both @track_request and @track_request(endpoint_name="...")
    if func is None:
        return decorator
    return decorator(func)
