FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application with conditional reload
CMD if [ "$ENVIRONMENT" = "development" ]; then \
        uvicorn main:app --host ${HOST} --port ${PORT} --reload; \
    else \
        uvicorn main:app --host ${HOST} --port ${PORT}; \
    fi 