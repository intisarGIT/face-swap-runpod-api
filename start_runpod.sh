#!/bin/bash

# RunPod startup script for Face Swap API
set -e

echo "Starting Face Swap API setup..."

# Update system packages
apt-get update
apt-get install -y python3 python3-pip python3-dev build-essential cmake libopencv-dev wget curl

# Upgrade pip
pip3 install --upgrade pip setuptools wheel

# Install Python dependencies
pip3 install -r requirements-api.txt

echo "Setup complete! Starting Face Swap API..."

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
