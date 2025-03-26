#!/bin/bash

# Test the Chatwoot webhook integration
curl -X POST "http://localhost:8080/webhook" \
  -H "Content-Type: application/json" \
  -d '{ 
    "event": "message_created", 
    "message": { 
      "id": 123, 
      "content": "Test AI message with entity id customer_123", 
      "sender": { 
        "id": 456, 
        "type": "contact" 
      } 
    }, 
    "conversation": { 
      "id": 789 
    } 
  }'
