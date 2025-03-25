#!/usr/bin/env python3
"""
Test script for the LangChain agent implementation.
This allows you to test your agent's responses without setting up Chatwoot.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent executor from our main script
# Note: In a real implementation, you'd structure your code better
# but for testing purposes, we're importing directly
from app import agent_executor, extract_entity_ids

def test_agent():
    """
    Simple interactive test for the agent.
    Allows you to input messages and see how the agent responds.
    """
    print("=" * 50)
    print("LangChain Agent Tester")
    print("Type 'exit' to quit")
    print("=" * 50)
    
    while True:
        # Get user input
        user_input = input("\nCustomer message: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        print("\nProcessing...")
        
        # Extract potential entity IDs (for debugging)
        entities = extract_entity_ids(user_input)
        if entities:
            print(f"Detected entities: {json.dumps(entities, indent=2)}")
        
        # Process with the agent
        try:
            response = agent_executor.invoke({
                "input": user_input
            })
            
            print("\n" + "=" * 50)
            print("Agent Response:")
            print(response["output"])
            print("=" * 50)
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_agent()
