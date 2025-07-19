# Use Ubuntu base image - we'll add CUDA support via Python packages
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    libopencv-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements-api.txt .

# Install Python dependencies with increased timeout and retries
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir --timeout 1000 --retries 5 -r requirements-api.txt

# Copy the application code
COPY main_fixed.py .
COPY main.py .
# The ONNX model will be downloaded on first run by the main_fixed.py script
# This keeps the docker image smaller and ensures the latest model is used.

# Create directories for models (InsightFace will download to ~/.insightface)
RUN mkdir -p /root/.insightface/models

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main_fixed:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
