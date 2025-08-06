FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs /app/structured_todos

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Run the application
CMD ["python", "-u", "main.py"]