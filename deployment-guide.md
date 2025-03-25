# Deployment Guide: LangChain + Chatwoot Integration

This guide will help you deploy your LangChain agent that integrates with Chatwoot and connects to ERPNext, Splynx, and UNMS systems to retrieve customer information.

## Prerequisites

- Python 3.8+ installed
- Access to ERPNext, Splynx, and UNMS systems with API credentials
- A Chatwoot account with API access
- An OpenAI API key

## Step 1: Set Up the Environment

1. Clone the repository or create a new directory for your project
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install langchain langchain-openai openai python-dotenv requests flask gunicorn
   ```
4. Copy the `.env.sample` file to `.env` and fill in your actual API keys and credentials:
   ```bash
   cp .env.sample .env
   # Edit .env with your favorite text editor
   ```

## Step 2: Configure Chatwoot Webhooks

1. Log in to your Chatwoot admin dashboard
2. Go to Settings > Integrations > Webhooks
3. Add a new webhook with the following settings:
   - URL: `https://your-server-address.com/webhook/chatwoot`
   - Events to notify: Select at least "Message Created"
   - Advanced Options: You can optionally add a secret key for additional security

## Step 3: Test Locally

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Use a tool like ngrok to expose your local server to the internet (for testing):
   ```bash
   ngrok http 5000
   ```
3. Update your Chatwoot webhook URL with the ngrok URL
4. Start a conversation in Chatwoot to test the integration

## Step 4: Production Deployment

For production, you should deploy to a proper server environment. Here are some options:

### Option 1: Deploy with Docker

1. Create a Dockerfile:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
   ```

2. Create a `requirements.txt` file:
   ```
   langchain
   langchain-openai
   openai
   python-dotenv
   requests
   flask
   gunicorn
   ```

3. Build and run the Docker image:
   ```bash
   docker build -t chatwoot-langchain .
   docker run -p 5000:5000 --env-file .env chatwoot-langchain
   ```

### Option 1b: Deploy to Private Cloud with Docker

1. Prepare your Docker image as described above.

2. Create a `docker-compose.yml` file for easier management:
   ```yaml
   version: '3'
   
   services:
     chatwoot-langchain:
       build: .
       ports:
         - "5000:5000"
       env_file:
         - .env
       restart: unless-stopped
       volumes:
         - ./logs:/app/logs
   ```

3. For private cloud deployment:
   - Push your Docker image to a private registry:
     ```bash
     # Tag your image for your private registry
     docker tag chatwoot-langchain your-registry.example.com/chatwoot-langchain
     
     # Push to your private registry
     docker push your-registry.example.com/chatwoot-langchain
     ```
   
   - On your private cloud server:
     ```bash
     # Pull the image from your private registry
     docker pull your-registry.example.com/chatwoot-langchain
     
     # Run with docker-compose
     docker-compose up -d
     ```

4. For high availability, consider using Docker Swarm or Kubernetes:
   ```bash
   # Initialize Docker Swarm
   docker swarm init
   
   # Deploy as a stack
   docker stack deploy -c docker-compose.yml chatwoot-langchain
   ```

### Option 2: Deploy to Cloud Platform

#### Heroku
```bash
# Install the Heroku CLI
heroku create your-app-name
git push heroku main
heroku config:set $(cat .env)
```

#### AWS Elastic Beanstalk
1. Install the EB CLI
2. Initialize your EB application:
   ```bash
   eb init -p python-3.8 chatwoot-langchain
   eb create chatwoot-langchain-env
   ```
   
3. Set environment variables through the AWS Console or CLI

## Step 5: Monitor and Maintain

1. Set up logging to monitor the application:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. Consider implementing a more robust error handling and retry mechanism for API calls

3. Regularly review the conversations to ensure the agent is providing accurate responses

## Advanced Customization

### Improving the Agent

1. Fine-tune the system prompt to better match your company's tone and style
2. Add more tools to retrieve additional types of information
3. Implement custom logic to handle specific customer scenarios

### Enhanced Security

1. Add JWT or OAuth authentication to the webhook endpoint
2. Implement rate limiting