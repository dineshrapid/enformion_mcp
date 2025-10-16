# Use official Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Install system dependencies required for running requests, uvicorn, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080


# Set environment variables for Enformion API credentials
# (You can override these at runtime with docker -e)
ENV GALAXY_AP_NAME=your_profile_name
ENV GALAXY_AP_PASSWORD=your_profile_password

# Run the MCP server
CMD ["python", "src/main.py"]
