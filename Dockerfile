# syntax = docker/dockerfile:1

# Use Python base image
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY server.py .

# Expose port
EXPOSE 8000

# Start the server
CMD ["python", "server.py"]
