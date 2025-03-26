#!/bin/bash

# Replace this with your actual Deepseek API key
API_KEY="your_deepseek_api_key_here"

# Test the Deepseek API with a simple request
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
        "model": "deepseek-chat",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello!"}
        ],
        "stream": false
      }'
