#!/usr/bin/env python3
"""
Test script for failure injection functionality
"""

import json
import logging
import time
from locust.failure_injection import FailureInjector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_failure_injection")

def test_failure_injector():
    """Test the FailureInjector class"""
    # Create a mock admin API endpoint
    admin_url = "http://localhost:5001"  # This won't actually be used in our test
    
    # Initialize the failure injector
    injector = FailureInjector(admin_url)
    
    # Test creating a failure scenario
    logger.info("Testing failure injection...")
    
    # Since we can't actually call the API, we'll just test the object creation
    # and metric recording functionality
    
    # Test the failure counter metric
    injector.failure_counter.labels(
        scenario="redis_outage", 
        target_service="redis"
    ).inc()
    
    # Test the active failure gauge metric
    injector.active_failure_gauge.labels(
        scenario="redis_outage", 
        target_service="redis"
    ).set(1)
    
    # Print the metric registry
    for metric in injector.failure_counter._registry.collect():
        for sample in metric.samples:
            logger.info(f"Metric: {sample.name}, Labels: {sample.labels}, Value: {sample.value}")
    
    logger.info("Failure injection test completed")

if __name__ == "__main__":
    test_failure_injector()
