"""
Simplified circuit breaker implementation for testing the Chatwoot webhook functionality.
"""
class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, name):
        self.name = name
        self.state = "closed"  # closed, open, half-open
        
    def __str__(self):
        return f"CircuitBreaker({self.name}, state={self.state})"

# Create circuit breaker instances
erp_circuit = CircuitBreaker("erp")
splynx_circuit = CircuitBreaker("splynx")
unms_circuit = CircuitBreaker("unms")
