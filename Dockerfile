# Standalone Dockerfile for the example repository
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (graphviz for blueprint rendering)
RUN apt-get update && apt-get install -y \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Default command to run the orchestrator
CMD ["python", "full_example.py"]