# LangChain-Chatwoot Agent Integration

This project implements separate sales and support agents for an Internet Service Provider (ISP) that handle specific functions within Chatwoot conversations. The agents use LangChain for orchestration, ERPNext for sales capabilities, and Splynx/UNMS for support functionalities.

## Features

- **Specialized Agents**: 
  - **SalesAgent**: Handles sales inquiries, promotions, and service plans
  - **SupportAgent**: Manages technical support, outages, and customer issues
- **Conversation Context Management**: Maintains context across messages
- **Integration with Multiple Systems**:
  - **Chatwoot**: For customer conversations
  - **ERPNext**: For sales information (service plans, promotions, etc.)
  - **Splynx**: For billing and customer information
  - **UNMS**: For network monitoring and device status

## Architecture

The system consists of the following components:

1. **Flask Web Server** (`app.py`): Handles Chatwoot webhooks and routes messages to the appropriate handler
2. **Agent Classes**:
   - **SalesAgent** (`agents/sales_agent.py`): Implements the sales-specific agent functionality
   - **SupportAgent** (`agents/support_agent.py`): Implements the support-specific agent functionality
3. **LangChain Integration** (`langchain_integration.py`): Manages the integration with Chatwoot and routes messages to the appropriate agent
4. **Semantic Cache** (`semantic_cache.py`): Caches responses to improve performance
5. **Prometheus Metrics** (`prometheus_metrics.py`): Tracks performance metrics for monitoring

## Setup

### Prerequisites

- Python 3.8+
- Chatwoot account with API access
- ERPNext instance (or mock for testing)
- Splynx instance (or mock for testing)
- UNMS instance (or mock for testing)
- OpenAI API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   # OpenAI
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4-turbo for better results
   
   # Chatwoot
   CHATWOOT_API_KEY=your_chatwoot_api_key
   CHATWOOT_ACCOUNT_ID=your_chatwoot_account_id
   CHATWOOT_BASE_URL=https://your_chatwoot_instance.com
   
   # ERPNext
   ERPNEXT_API_KEY=your_erpnext_api_key
   ERPNEXT_API_SECRET=your_erpnext_api_secret
   ERPNEXT_BASE_URL=https://your_erpnext_instance.com
   
   # Splynx
   SPLYNX_API_KEY=your_splynx_api_key
   SPLYNX_API_SECRET=your_splynx_api_secret
   SPLYNX_BASE_URL=https://your_splynx_instance.com
   
   # UNMS
   UNMS_API_KEY=your_unms_api_key
   UNMS_BASE_URL=https://your_unms_instance.com
   
   # Application settings
   PORT=5000
   DEBUG=True
   TEST_MODE=True  # Set to False for production
   ```

### Running the Application

```
python app.py
```

The server will start on the port specified in the `.env` file (default: 5000).

### Testing

#### Comprehensive Test Suite

The project includes a comprehensive test suite that covers all agent classes and their functionality:

```bash
python run_tests.py
```

This will run all tests and generate a coverage report in the terminal and an HTML coverage report in the `coverage_html` directory.

The test suite includes:

1. **Unit Tests**:
   - `test_agent_classes.py`: Tests for the SalesAgent and SupportAgent classes
   - `test_dual_role_agent.py`: Tests for the DualRoleAgent class
   - `test_semantic_cache.py`: Tests for the SemanticCache class
   - `test_integration.py`: Integration tests for the langchain_integration module

2. **Test Coverage**:
   - The test suite achieves over 90% code coverage for the agent classes
   - Tests include initialization, message processing, error handling, caching, and entity extraction

3. **Mock Implementations**:
   - Tests use mock implementations to avoid external dependencies
   - Mock context managers simulate conversation context
   - Mock tools simulate agent capabilities

To run specific tests, you can use:

```bash
python -m unittest tests/test_agent_classes.py
```

#### Test Environment

For testing, set the following environment variables:

```
TEST_MODE=true
OPENAI_API_KEY=your_test_key  # Can be any value in test mode
```

These can be set in the `.env.test` file, which is loaded automatically when running tests.

## Configuring Chatwoot

1. In your Chatwoot account, go to Settings > Integrations > Webhooks
2. Add a new webhook with the URL of your deployed application (e.g., `https://your-server.com/webhook/chatwoot`)
3. Select the events you want to receive (at minimum, select "Message Created")
4. Save the webhook configuration

## Development

### Adding New Tools

To add a new tool to an agent:

1. Implement the tool function in the appropriate agent class
2. Add the tool to the `tools` list with a descriptive name and description
3. Update the agent prompt templates to include the new tool

### Agent Implementation

The agents are implemented using LangChain's agent framework:

1. **SalesAgent**: Specializes in handling sales inquiries, with tools for:
   - Retrieving service plans
   - Checking promotions
   - Creating quotes
   - Looking up customer information

2. **SupportAgent**: Specializes in handling support inquiries, with tools for:
   - Checking network status
   - Diagnosing connection issues
   - Creating support tickets
   - Looking up device information

Each agent has its own prompt template and set of tools tailored to its specific role.

## Production Deployment

For production deployment, we use Docker to containerize the application. Follow these steps to deploy:

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t chatwoot-langchain .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 --env-file .env chatwoot-langchain
   ```

### Docker Compose Deployment

For a more complete setup with proper restart policies and volume mounting:

1. Deploy using docker-compose:
   ```bash
   docker-compose up -d
   ```

2. Check the logs:
   ```bash
   docker-compose logs -f
   ```

## Team Collaboration

We follow the GitFlow branching strategy:

1. `main` branch: Production-ready code
2. `develop` branch: Main development branch
3. `feature/*` branches: For new features
4. `bugfix/*` branches: For bug fixes
5. `hotfix/*` branches: For critical production fixes
6. `release/*` branches: For preparing releases

When working on a new feature or fix:

1. Create a new branch from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. Push your branch and create a pull request to `develop`:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. After code review and approval, merge your pull request into `develop`

## Performance Testing

To test the performance of the application in a production-like environment:

### Setup Performance Testing Environment

1. Create a `.env.perf` file with your performance testing configuration
2. Deploy the performance testing environment:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.perf.yml up -d
   ```

### Running Load Tests

1. Access the Locust web interface at http://localhost:8089
2. Configure the number of users and spawn rate
3. Start the test and monitor the results

### Monitoring Performance

1. Access Grafana at http://localhost:3000 (default credentials: admin/admin)
2. Configure dashboards to monitor:
   - Response times
   - Throughput
   - Error rates
   - CPU and memory usage

### Performance Test Reports

After running performance tests, create a report using the template in the `deployment-guide.md` file, including:

1. Test configuration details
2. Performance metrics
3. Observations and recommendations

## CI/CD Integration

The repository includes GitHub Actions workflows for:

1. Automated testing on pushes to `main` and `develop` branches
2. Automated testing on pull requests to `main` and `develop`

To view the workflow configurations, check the `.github/workflows` directory.

## Production Considerations

When deploying to production:

1. Set `TEST_MODE=False` in the `.env` file
2. Implement proper database storage for conversation context instead of in-memory storage
3. Add authentication to the API endpoints
4. Set up monitoring and logging
5. Consider implementing rate limiting for the OpenAI API calls
6. Use a reverse proxy like Nginx for SSL termination and load balancing

## Troubleshooting

For common issues and their solutions, refer to the "Troubleshooting Common Issues" section in the `deployment-guide.md` file.

## License

MIT
