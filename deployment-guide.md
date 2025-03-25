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

## Step 5: Team Collaboration and Performance Testing

### Setting Up for Team Collaboration

1. Share the repository with your team:
   ```bash
   # Clone the repository
   git clone https://github.com/michaelayoade/chatwoot-ai.git
   cd chatwoot-ai
   
   # Create a new branch for your work
   git checkout -b feature/your-feature-name
   ```

2. Follow the GitFlow branching strategy:
   - `main` branch: Production-ready code
   - `develop` branch: Main development branch
   - `feature/*` branches: For new features
   - `bugfix/*` branches: For bug fixes
   - `hotfix/*` branches: For critical production fixes
   - `release/*` branches: For preparing releases

3. Create a shared development environment:
   ```bash
   # Deploy the develop branch to a staging server
   git checkout develop
   # Follow the deployment steps above but use a separate staging environment
   ```

### Performance Testing

1. Set up a performance testing environment:
   ```bash
   # Deploy a separate instance for performance testing
   docker-compose -f docker-compose.yml -f docker-compose.perf.yml up -d
   ```

2. Use a load testing tool like Locust or Apache JMeter to simulate multiple users:
   ```bash
   # Install Locust
   pip install locust
   
   # Create a locustfile.py with test scenarios
   # Run Locust
   locust -f locustfile.py
   ```

3. Key metrics to monitor:
   - Response time: Average time to respond to user queries
   - Throughput: Number of queries processed per minute
   - Error rate: Percentage of failed requests
   - CPU/Memory usage: Resource utilization during peak loads

4. Create a performance testing report template:
   ```markdown
   # Performance Test Report
   
   ## Test Configuration
   - Date: YYYY-MM-DD
   - Environment: [Staging/Production]
   - Number of simulated users: X
   - Test duration: Y minutes
   
   ## Results
   - Average response time: Z ms
   - Throughput: X requests/minute
   - Error rate: Y%
   - Peak memory usage: Z MB
   
   ## Observations and Recommendations
   - [Add your observations here]
   - [Add your recommendations here]
   ```

## Step 6: CI/CD Integration

1. GitHub Actions workflow is already set up for testing:
   - Tests run automatically on pushes to `main` and `develop` branches
   - Tests run on pull requests targeting `main` and `develop` branches

2. Extend the workflow for continuous deployment:
   ```yaml
   # Add to .github/workflows/deploy.yml
   name: Deploy to Production
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Build and push Docker image
           uses: docker/build-push-action@v2
           with:
             context: .
             push: true
             tags: your-registry.example.com/chatwoot-langchain:latest
         
         - name: Deploy to production
           run: |
             # Add your deployment commands here
             # For example, SSH into your server and pull the latest image
   ```

3. Set up automatic deployment to staging for the develop branch:
   ```yaml
   # Add to .github/workflows/deploy-staging.yml
   name: Deploy to Staging
   
   on:
     push:
       branches: [ develop ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Build and push Docker image
           uses: docker/build-push-action@v2
           with:
             context: .
             push: true
             tags: your-registry.example.com/chatwoot-langchain:staging
         
         - name: Deploy to staging
           run: |
             # Add your staging deployment commands here
   ```

## Step 7: Monitor and Maintain

1. Set up logging to monitor the application:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. Consider implementing a more robust error handling and retry mechanism for API calls

3. Regularly review the conversations to ensure the agent is providing accurate responses

4. Set up monitoring and alerting:
   - Use Prometheus and Grafana for metrics visualization
   - Set up alerts for high error rates or response times
   - Monitor OpenAI API usage to control costs

## Advanced Customization

### Improving the Agent

1. Fine-tune the system prompt to better match your company's tone and style
2. Add more tools to retrieve additional types of information
3. Implement custom logic to handle specific customer scenarios

### Enhanced Security

1. Add JWT or OAuth authentication to the webhook endpoint
2. Implement rate limiting
3. Set up IP allowlisting for your webhook endpoints
4. Regularly rotate API keys and credentials

## Troubleshooting Common Issues

1. **OpenAI API errors**: Check your API key and ensure you have sufficient credits
2. **Webhook not receiving events**: Verify the webhook URL is correctly configured in Chatwoot
3. **Agent not responding correctly**: Review the system prompts and ensure all tools are functioning
4. **High latency**: Check network connectivity to external APIs and consider caching frequently accessed data