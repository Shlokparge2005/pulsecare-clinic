# PulseCare Clinic & Emergency Coordination Hub
# Optimized for Google Cloud Run (Container runtime)

FROM python:3.12-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data

# Cloud Run injects $PORT environment variable
EXPOSE 8080

# Run with Gunicorn WSGI production server
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 app:app
