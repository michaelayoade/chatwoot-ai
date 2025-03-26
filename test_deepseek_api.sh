#!/bin/bash

# Replace this with your actual Deepseek API key
API_KEY="your_deepseek_api_key_here"

# Test the Deepseek API with a simple request
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {
        "role": "user",
        "content": "What internet plans do you offer?"
      }
    ],
    "temperature": 0.3
  }'
