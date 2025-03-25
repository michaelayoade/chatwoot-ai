#!/bin/bash

# Check if DEEPSEEK_API_KEY is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
  echo "Error: DEEPSEEK_API_KEY environment variable is not set."
  echo "Please set it before running this script:"
  echo "export DEEPSEEK_API_KEY=your_api_key_here"
  exit 1
fi

# Export the API key for docker-compose
export DEEPSEEK_API_KEY

# Start the Docker container
docker-compose up
