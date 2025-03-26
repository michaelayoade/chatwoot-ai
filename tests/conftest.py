import os
from dotenv import load_dotenv

def pytest_configure(config):
    """Load environment variables before tests run"""
    load_dotenv()
    
    # Set test-specific environment variables
    os.environ["OPENAI_API_KEY"] = "sk-test-key"    
    