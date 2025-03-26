import time
from collections import deque

class RateLimiter:
    def __init__(self, limit=10, window=1.0):
        self.limit = limit
        self.window = window
        self.requests = deque()
    
    def allow_request(self):
        current_time = time.time()
        
        # Remove requests older than the window
        while self.requests and self.requests[0] < current_time - self.window:
            self.requests.popleft()
        
        # Check if we're at the limit
        if len(self.requests) >= self.limit:
            return False
            
        # Add this request timestamp
        self.requests.append(current_time)
        return True
