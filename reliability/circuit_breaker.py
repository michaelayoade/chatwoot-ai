import time
from functools import wraps

class CircuitBreaker:
    def __init__(self, fail_threshold=5, reset_timeout=60):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "closed"  # closed, open
        self.last_failure_time = None
        
    def __enter__(self):
        if self.state == "open":
            # Check if timeout has elapsed
            if self.last_failure_time and time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "closed"
                self.failures = 0
            else:
                raise Exception("Circuit breaker is open")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.fail_threshold:
                self.state = "open"
            return False  # re-raise the exception
        return True
    
    def is_open(self):
        return self.state == "open"
