# Use official Python slim image as base
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy only the pyproject file first to leverage Docker cache for dependencies
COPY pyproject.toml ./

# Install Python dependencies

# Install curl and uv package manager
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# uv sync 
RUN uv sync

# Copy the rest of the application code
COPY . .

# Expose the default FastAPI port
EXPOSE 8000

# Default command to run the application
CMD ["uvicorn", "app.routes:app", "--host", "0.0.0.0", "--port", "8000"]
