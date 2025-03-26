"""
Test script for Deepseek integration
"""
import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Initialize Deepseek
model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
# Remove 'Bearer ' prefix if present
if deepseek_api_key.startswith("Bearer "):
    deepseek_api_key = deepseek_api_key[7:]

llm = ChatDeepSeek(
    api_key=deepseek_api_key,
    temperature=0.3,
    model_name=model_name
)

def test_deepseek():
    """Test Deepseek API with a simple query"""
    print("Testing Deepseek API...")
    try:
        response = llm.invoke([HumanMessage(content="What internet plans do you offer?")])
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_deepseek()
    print(f"Test {'succeeded' if success else 'failed'}")
