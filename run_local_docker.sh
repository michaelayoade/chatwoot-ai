#!/bin/bash
# Script to build and run the Docker container locally

# Set variables
PROJECT_DIR="/Users/michaelayoade/CascadeProjects/Langchain"
CONTAINER_NAME="chatwoot-langchain-local"

# Step 1: Build the Docker image
echo "Building Docker image..."
docker build -t $CONTAINER_NAME $PROJECT_DIR

# Step 2: Run the Docker container
echo "Running Docker container..."
docker run -d --name $CONTAINER_NAME \
  -p 5000:5000 \
  --env-file $PROJECT_DIR/.env \
  -v $PROJECT_DIR/logs:/app/logs \
  $CONTAINER_NAME

# Step 3: Check the container status
echo "Checking container status..."
docker ps | grep $CONTAINER_NAME

echo "Docker container is running at http://localhost:5000"
echo "To test the webhook, use: curl -X POST \"http://localhost:5000/webhook\" -H \"Content-Type: application/json\" -d '{ \"event\": \"message_created\", \"message\": { \"id\": 123, \"content\": \"Test AI message with entity id customer_123\", \"sender\": { \"id\": 456, \"type\": \"contact\" } }, \"conversation\": { \"id\": 789 } }'"
echo "To view logs: docker logs $CONTAINER_NAME"
echo "To stop the container: docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
