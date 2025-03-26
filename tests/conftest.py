import os
import sys
from dotenv import load_dotenv

def pytest_configure(config):
    """Load environment variables before tests run"""
    load_dotenv()
    
    # Set up testing environment
    os.environ['TESTING'] = 'True'
    os.environ['OPENAI_API_KEY'] = 'sk-test-key'
    os.environ['DEEPSEEK_API_KEY'] = 'test-key'