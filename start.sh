#!/bin/bash

# 1. Start the agent in the background (for AgentVerse/DeltaV access)
echo "Starting uAgents Agent..."
python backend/src/agent.py &

# 2. Start the Flask API server in the foreground (for web frontend)
echo "Starting Flask API Server..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 backend.api_server:app