FROM python:3.9-slim

WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    TEST_MODE=false \
    DEEPSEEK_API=true

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN useradd -m appuser && \
    mkdir -p /app/data/contexts /app/logs && \
    chown -R appuser:appuser /app

# Copy only essential files, re-creating them with clean encoding
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy app.py with encoding check
COPY --chown=appuser:appuser app.py /tmp/app.py
RUN cat /tmp/app.py | tr -d '\000' > /app/app.py && rm /tmp/app.py

# Copy key modules with encoding cleaning
COPY --chown=appuser:appuser agent_prompts.py /tmp/agent_prompts.py
RUN cat /tmp/agent_prompts.py | tr -d '\000' > /app/agent_prompts.py && rm /tmp/agent_prompts.py

COPY --chown=appuser:appuser reliability.py /tmp/reliability.py
RUN cat /tmp/reliability.py | tr -d '\000' > /app/reliability.py && rm /tmp/reliability.py

COPY --chown=appuser:appuser semantic_cache.py /tmp/semantic_cache.py
RUN cat /tmp/semantic_cache.py | tr -d '\000' > /app/semantic_cache.py && rm /tmp/semantic_cache.py

COPY --chown=appuser:appuser prometheus_metrics.py /tmp/prometheus_metrics.py
RUN cat /tmp/prometheus_metrics.py | tr -d '\000' > /app/prometheus_metrics.py && rm /tmp/prometheus_metrics.py

COPY --chown=appuser:appuser logger_config.py /tmp/logger_config.py
RUN cat /tmp/logger_config.py | tr -d '\000' > /app/logger_config.py && rm /tmp/logger_config.py

COPY --chown=appuser:appuser langchain_integration.py /tmp/langchain_integration.py
RUN cat /tmp/langchain_integration.py | tr -d '\000' > /app/langchain_integration.py && rm /tmp/langchain_integration.py

# Copy api_circuit_breaker.py with encoding cleaning
COPY --chown=appuser:appuser api_circuit_breaker.py /tmp/api_circuit_breaker.py
RUN cat /tmp/api_circuit_breaker.py | tr -d '\000' > /app/api_circuit_breaker.py && rm /tmp/api_circuit_breaker.py

# Copy rate_limiter.py with encoding cleaning
COPY --chown=appuser:appuser rate_limiter.py /tmp/rate_limiter.py
RUN cat /tmp/rate_limiter.py | tr -d '\000' > /app/rate_limiter.py && rm /tmp/rate_limiter.py

# Create directories for modules
RUN mkdir -p /app/agents /app/handlers /app/utils /app/tools

# Set the PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Copy agents directory
COPY --chown=appuser:appuser agents/*.py /tmp/
RUN for file in /tmp/*.py; do \
        filename=$(basename $file); \
        cat $file | tr -d '\000' > /app/agents/$filename; \
    done && \
    rm /tmp/*.py

# Copy handlers directory
COPY --chown=appuser:appuser handlers/*.py /tmp/
RUN for file in /tmp/*.py; do \
        filename=$(basename $file); \
        cat $file | tr -d '\000' > /app/handlers/$filename; \
    done && \
    rm /tmp/*.py

# Copy utils directory
COPY --chown=appuser:appuser utils/*.py /tmp/
RUN for file in /tmp/*.py; do \
        filename=$(basename $file); \
        cat $file | tr -d '\000' > /app/utils/$filename; \
    done && \
    rm /tmp/*.py

# Copy tools directory
COPY --chown=appuser:appuser tools/*.py /tmp/
RUN for file in /tmp/*.py; do \
        filename=$(basename $file); \
        cat $file | tr -d '\000' > /app/tools/$filename; \
    done && \
    rm /tmp/*.py

# Switch to the non-root user
USER appuser

# Expose the specified port
EXPOSE 8080

# Add basic healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Use gunicorn for production-ready server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "app:app"]
