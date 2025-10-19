#!/bin/bash

# 1. Start the agent in the background
echo "Starting Agent..."
python backend/agent.py &

# 2. Start the web gateway in the foreground
echo "Starting Gateway..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 backend.gateway:app