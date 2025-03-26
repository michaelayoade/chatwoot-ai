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

1. In your Chatwoot account, go to Settings > Integrations > Webhooks
2. Add a new webhook with the URL of your deployed application (e.g., `https://your-app.com/webhook/chatwoot`)
3. Select the events you want to trigger the webhook (at minimum, select "Message Created")
4. Save the webhook configuration

### Webhook Response Handling

The integration handles webhook responses from Chatwoot and processes messages using the LangChain agent. The system has been updated to properly handle response formats:

1. The `process_message` function in `langchain_integration.py` returns a string response instead of a tuple
2. The `process_webhook` method in `ChatwootHandler` extracts the response text if it receives a tuple (response, metadata)
3. The Flask app ensures the response is properly formatted before returning it to Chatwoot

These changes ensure that the webhook functionality works correctly and prevents the "unhashable type: 'dict'" error that could occur when processing entity IDs.

### Important Notes About Chatwoot Webhook Configuration

- The webhook endpoint `/webhook/chatwoot` is specifically designed to handle Chatwoot's webhook format
- Ensure your server is accessible from the internet so Chatwoot can send webhook events
- The integration handles replies via Chatwoot's API, using the API key configured in your `.env` file
- For debugging webhook issues, check the application logs for detailed information about incoming webhooks
- The webhook handler validates that messages are from contacts (customers) before processing them
- The system includes robust error handling and retry logic for API calls to ensure reliability
- Metrics are collected for both webhook processing and API calls to monitor system health
- The integration uses circuit breakers to prevent cascading failures if the Chatwoot API becomes unavailable
- Rate limiting is implemented to protect against API rate limits

### API Reply Mechanism

The integration uses Chatwoot's API to send replies back to conversations. Here's how it works:

1. When a webhook is received, the system extracts the conversation ID and message content
2. The message is processed by the LangChain agent to generate a response
3. The response is sent back to the conversation using the Chatwoot API
4. The system includes retry logic for API calls with exponential backoff
5. Failures are logged and metrics are collected for monitoring

### Testing Webhook Functionality

To test the webhook functionality without setting up a public endpoint:

1. Use the included test script:
   ```bash
   python test_chatwoot_simple.py
   ```

2. This script simulates webhook events and tests the processing logic
3. It runs in test mode, so no actual API calls are made to external services
4. You can modify the test data in the script to test different scenarios

### Reliability Features

The integration includes several reliability features to ensure robust operation:

1. **Structured Logging**: All operations are logged with structured data for easier debugging and monitoring
2. **Circuit Breakers**: Prevent cascading failures if external APIs become unavailable
3. **Rate Limiting**: Protect against API rate limits for all external services
4. **Retry Logic**: Automatically retry failed API calls with exponential backoff
5. **Metrics Collection**: Track performance and error rates for all operations
6. **Anomaly Detection**: Alert on unusual patterns in request rates, error rates, and latency
7. **Semantic Caching**: Reduce API calls and improve response times for similar queries

To test the reliability features:

```bash
python test_reliability.py
```

This script tests the circuit breaker and rate limiting functionality.

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

## Step 8: Reliability Components

The LangChain-Chatwoot integration includes several reliability components to ensure robust operation in production environments. This section explains how to configure and use these components.

### Structured Logging

We use `structlog` for structured, contextual logging that makes debugging and monitoring easier.

1. Configuration:
   ```python
   # In .env
   LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
   LOG_FORMAT=json  # Options: json, console
   ```

2. Log consumption:
   - In development: Logs are output to the console
   - In production: Logs are collected by your logging infrastructure (e.g., ELK, Loki)
   - Key metrics are extracted from logs and sent to Prometheus

### Anomaly Detection Alerts

Prometheus alert rules are configured to detect anomalies in the system's behavior:

1. Alert configuration:
   ```bash
   # Located in prometheus/alert_rules.yml
   # Alerts are managed by AlertManager
   ```

2. Key alerts include:
   - High error rates (>5% of requests failing)
   - Unusual request rate patterns (sudden spikes or drops)
   - API latency anomalies (responses taking >2s)
   - Circuit breaker state changes (open circuits)
   - Cache miss rates (>50% miss rate)
   - Rate limiting thresholds (>80% of limit reached)
   - LLM token usage (approaching quota limits)
   - Redis memory usage (>80% capacity)

3. Alert notification channels:
   - Email notifications for critical alerts
   - Slack integration for team notifications
   - PagerDuty for on-call rotations

### Synthetic Transaction Monitoring

Synthetic monitoring simulates user interactions to proactively detect issues:

1. Configuration:
   ```bash
   # Run the synthetic monitor
   python monitoring/synthetic_monitor.py --url http://your-app-url:5001
   
   # For scheduled monitoring (every 5 minutes)
   python monitoring/synthetic_monitor.py --url http://your-app-url:5001 --schedule --interval 300
   
   # To push metrics to Prometheus Pushgateway
   python monitoring/synthetic_monitor.py --url http://your-app-url:5001 --pushgateway http://pushgateway:9091
   ```

2. Monitored conversation flows:
   - Sales inquiries
   - Technical support requests
   - Account inquiries
   - Order status checks

3. Metrics collected:
   - Success rate for each conversation flow
   - End-to-end response time
   - Context maintenance verification
   - Step-by-step completion status

### Circuit Breakers

Circuit breakers protect the system from cascading failures when downstream services are unavailable:

1. Configuration:
   ```python
   # In .env
   CIRCUIT_BREAKER_FAILURE_THRESHOLD=5  # Open after 5 consecutive failures
   CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30  # Wait 30 seconds before half-open state
   CIRCUIT_BREAKER_HALF_OPEN_REQUESTS=3  # Allow 3 requests in half-open state
   ```

2. Monitoring circuit breaker status:
   - Check the `/metrics` endpoint for circuit breaker metrics
   - Set up alerts when circuits remain open for extended periods
   - Monitor the circuit state transitions in Grafana

### Rate Limiting

Rate limiting protects external APIs from excessive calls and helps manage costs.

1. Configuration:
   ```python
   # In .env
   RATE_LIMIT_OPENAI_RPM=60  # Requests per minute for OpenAI API
   RATE_LIMIT_ERPNEXT_RPM=30  # Requests per minute for ERPNext API
   RATE_LIMIT_SPLYNX_RPM=30   # Requests per minute for Splynx API
   RATE_LIMIT_UNMS_RPM=30     # Requests per minute for UNMS API
   ```

2. Best practices:
   - Set rate limits slightly below the documented API limits (80-90%) to provide buffer
   - Adjust rate limits based on your subscription tier for each service
   - Monitor rate limit errors to identify potential bottlenecks

### Failure Injection Testing

The system includes tools for simulating failures to test resilience:

1. Running failure tests:
   ```bash
   # Start the Locust UI for failure injection testing
   cd locust && python -m locust -f failure_injection.py
   
   # Or run headless with specific failure scenario
   cd locust && python -m locust -f failure_injection.py --headless -u 10 -r 1 -t 5m --host http://your-app-url:5001
   ```

2. Available failure scenarios:
   - Redis outage: Simulates Redis service unavailability
   - LLM API outage: Simulates OpenAI API failures
   - Network partition: Simulates network connectivity issues
   - High latency: Introduces artificial delays in responses
   - Random errors: Introduces random 500 errors at configurable rates

3. Admin API for failure control:
   ```bash
   # Activate a failure scenario
   curl -X POST http://your-app-url:5001/admin/failures \
     -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"scenario": "redis_outage", "duration_seconds": 300}'
   
   # Check active failures
   curl http://your-app-url:5001/admin/failures \
     -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
   
   # Clear all active failures
   curl -X DELETE http://your-app-url:5001/admin/failures \
     -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
   ```

4. Security considerations:
   - The Admin API requires a secure API key defined in your .env file
   - Failure injection should only be enabled in testing environments
   - Production deployments should have the Admin API disabled or heavily restricted

## Step 9: Testing Strategy

### Unit Testing

1. Test each reliability component in isolation:
   ```bash
   # Run unit tests
   pytest tests/unit/
   ```

2. Key unit tests:
   - Circuit breaker behavior under various failure scenarios
   - Rate limiter enforcement and queuing
   - Semantic cache hit/miss logic
   - Structured logging format and content

### Integration Testing

1. Test components working together:
   ```bash
   # Run integration tests
   pytest tests/integration/
   ```

2. Key integration tests:
   - End-to-end message processing with mocked external services
   - Redis integration for context storage
   - Prometheus metrics collection accuracy
   - Error handling and recovery flows

### Load Testing with Locust

1. Create realistic conversation scenarios:
   ```python
   # locust/locustfile.py
   from locust import HttpUser, task, between
   
   class ConversationUser(HttpUser):
       wait_time = between(3, 10)
       
       @task(3)
       def sales_inquiry(self):
           # Simulate a sales conversation
           self.client.post("/test", json={
               "conversation_id": f"test-{self.user_id}",
               "message": "I'm interested in your fiber plans",
               "role": "sales"
           })
       
       @task(7)
       def support_inquiry(self):
           # Simulate a support conversation
           self.client.post("/test", json={
               "conversation_id": f"test-{self.user_id}",
               "message": "My internet is slow",
               "role": "support"
           })
           
       @task(2)
       def complex_inquiry(self):
           # Simulate a complex conversation with multiple turns
           # ...
   ```

2. Test failure scenarios:
   ```python
   @task(1)
   def test_circuit_breaker(self):
       # Force multiple API failures to trigger circuit breaker
       for _ in range(10):
           self.client.post("/test", json={
               "conversation_id": f"test-circuit-{self.user_id}",
               "message": "Check status of device DEV-INVALID",
               "role": "support"
           })
   ```

3. Measure recovery time:
   ```python
   @task
   def measure_recovery(self):
       # Record time before failure
       start_time = time.time()
       
       # Trigger failure
       # ...
       
       # Measure time until system recovers
       # ...
       
       recovery_time = time.time() - start_time
       self.environment.events.request.fire(
           request_type="recovery",
           name="system_recovery",
           response_time=recovery_time * 1000,
           response_length=0,
           exception=None,
       )
   ```

## Step 10: Performance Tuning

### Cache Optimization

1. Start with conservative settings:
   ```python
   # In .env
   SEMANTIC_CACHE_TTL=3600  # 1 hour TTL
   SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.85  # Moderate similarity threshold
   ```

2. Monitor and adjust:
   - Analyze cache hit rates from the `/cache/stats` endpoint
   - If hit rates are low, consider lowering the similarity threshold
   - If responses seem outdated, reduce the TTL
   - Consider different TTLs for different types of queries

### Circuit Breaker Configuration

1. Initial settings:
   ```python
   # In .env
   CIRCUIT_BREAKER_FAILURE_THRESHOLD=5  # Open after 5 consecutive failures
   CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30  # Wait 30 seconds before half-open state
   CIRCUIT_BREAKER_HALF_OPEN_REQUESTS=3  # Allow 3 requests in half-open state
   ```

2. Tuning recommendations:
   - For critical APIs, use higher thresholds (8-10 failures)
   - For non-critical APIs, use lower thresholds (3-5 failures)
   - Adjust recovery timeout based on observed API recovery patterns
   - Monitor circuit breaker state transitions to identify problematic services

### Rate Limiter Optimization

1. Initial settings:
   ```python
   # In .env
   RATE_LIMIT_OPENAI_RPM=60  # 60 requests per minute
   RATE_LIMIT_QUEUE_SIZE=100  # Queue up to 100 requests
   RATE_LIMIT_QUEUE_TIMEOUT=30  # Wait up to 30 seconds in queue
   ```

2. Tuning recommendations:
   - Set rate limits to 80-90% of the documented API limits
   - Adjust queue size based on observed request patterns
   - Reduce queue timeout for user-facing requests
   - Increase queue timeout for background tasks

### Memory Management

1. Monitor memory usage:
   - Track memory usage through Prometheus metrics
   - Set up alerts for memory leaks or excessive usage

2. Optimization techniques:
   - Implement periodic cache cleanup for infrequently accessed items
   - Use streaming responses for large LLM outputs
   - Implement conversation context pruning for long conversations

## Troubleshooting Common Issues

1. **OpenAI API errors**: 
   - Check your API key and ensure you have sufficient credits
   - Verify that the circuit breaker is not open for the OpenAI API
   - Check rate limiting logs for throttling issues

2. **Webhook not receiving events**: 
   - Verify the webhook URL is correctly configured in Chatwoot
   - Check network connectivity and firewall rules
   - Inspect webhook logs for authentication or parsing errors

3. **Agent not responding correctly**: 
   - Review the system prompts and ensure all tools are functioning
   - Check the conversation context for missing or incorrect information
   - Verify that the semantic cache is not returning outdated responses

4. **High latency**: 
   - Check network connectivity to external APIs
   - Monitor cache hit rates and consider adjusting cache parameters
   - Verify that rate limiters are not causing excessive queuing
   - Check for circuit breakers in half-open or open state

5. **Redis connectivity issues**:
   - Verify Redis connection string and authentication
   - Check Redis memory usage and eviction policies
   - Consider implementing a fallback to file-based storage

6. **Prometheus metrics not appearing**:
   - Verify that metrics collection is enabled
   - Check Prometheus scrape configuration
   - Ensure the `/metrics` endpoint is accessible to Prometheus

## Documentation Resources

- [Structured Logging Guide](./docs/logging.md)
- [Circuit Breaker Pattern](./docs/circuit_breaker.md)
- [Rate Limiting Configuration](./docs/rate_limiting.md)
- [Semantic Caching](./docs/semantic_cache.md)
- [Monitoring Setup](./docs/monitoring.md)
- [Performance Tuning](./docs/performance.md)