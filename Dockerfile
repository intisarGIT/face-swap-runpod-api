# RunPod-optimized Dockerfile for face swap API
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-runpod.txt .
RUN pip install --no-cache-dir -r requirements-runpod.txt

# Copy application files
COPY main_fixed.py .
COPY main.py .
COPY runpod_handler.py .
COPY inswapper_128.fp16.onnx* ./
COPY inswapper_128.onnx* ./

# Create directory for InsightFace models
RUN mkdir -p /root/.insightface/models

# Make the main script executable
RUN chmod +x main_fixed.py

# RunPod serverless entry point
CMD ["python", "-u", "runpod_handler.py"]
