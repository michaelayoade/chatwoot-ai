from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter
import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

T = TypeVar('T')

class APIReliabilityWrapper:
    """
    A wrapper class that combines circuit breaker and rate limiting functionality
    for API calls to improve reliability.
    """
    
    def __init__(
        self,
        api_name: str = "default",
        circuit: Optional[CircuitBreaker] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        rate_limiter: Optional[RateLimiter] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        metrics_enabled: bool = False,
        logger=None
    ):
        """
        Initialize the APIReliabilityWrapper with optional circuit breaker and rate limiter.
        
        Args:
            api_name: Name of the API being wrapped (for logging and metrics)
            circuit: Circuit breaker instance (alternative name for circuit_breaker)
            circuit_breaker: Circuit breaker instance 
            rate_limiter: Rate limiter instance
            max_retries: Maximum number of retries for failed API calls
            retry_delay: Delay between retries in seconds
            metrics_enabled: Whether to collect metrics on API calls
            logger: Logger instance for logging events
        """
        self.api_name = api_name
        self.circuit_breaker = circuit or circuit_breaker or CircuitBreaker()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.metrics_enabled = metrics_enabled
        self.logger = logger or logging.getLogger(__name__)
    
    def wrap(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Wrap a function with circuit breaker and rate limiter protection.
        
        Args:
            func: The function to wrap
            
        Returns:
            Wrapped function with added reliability protections
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            for attempt in range(self.max_retries + 1):
                try:
                    # Check if circuit is open (too many failures)
                    if not self.circuit_breaker.allow_request():
                        self.logger.warning(f"{self.api_name}: Circuit breaker open, request blocked")
                        raise Exception(f"Service unavailable - circuit breaker open for {self.api_name}")
                    
                    # Check rate limiter
                    if not self.rate_limiter.allow_request():
                        self.logger.warning(f"{self.api_name}: Rate limit exceeded, request blocked")
                        raise Exception(f"Rate limit exceeded for {self.api_name}")
                    
                    # Make the API call
                    result = func(*args, **kwargs)
                    
                    # Record successful call
                    self.circuit_breaker.record_success()
                    
                    # Track metrics if enabled
                    if self.metrics_enabled:
                        duration = time.time() - start_time
                        self.logger.info(f"{self.api_name}: API call successful", 
                                         duration=duration, 
                                         attempts=attempt+1)
                    
                    return result
                    
                except Exception as e:
                    # Record the failure
                    self.circuit_breaker.record_failure()
                    
                    # Last attempt or non-retryable error
                    if attempt == self.max_retries:
                        if self.metrics_enabled:
                            duration = time.time() - start_time
                            self.logger.error(f"{self.api_name}: Max retries exceeded", 
                                             duration=duration, 
                                             error=str(e),
                                             attempts=attempt+1)
                        raise
                    
                    # Wait before retrying
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    self.logger.warning(f"{self.api_name}: Retrying after error: {str(e)}")
        
        return wrapper
