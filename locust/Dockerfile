FROM python:3.10-slim

WORKDIR /mnt/locust

# Install dependencies
RUN pip install --no-cache-dir locust requests

# Expose the required Locust ports
EXPOSE 8089 5557 5558

# Set Locust as the entrypoint
ENTRYPOINT ["locust"]
