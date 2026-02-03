FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY setup.py .

# Install the package
RUN pip install -e .

# Copy configuration
COPY config/ config/

# Create directories for models
RUN mkdir -p /app/models

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose metrics port
EXPOSE 8000

# Run the DIS agent
CMD ["python", "-m", "dis_k8s.main"]
