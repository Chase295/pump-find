#!/bin/bash

# Start FastAPI in background
uvicorn unified_service:app --host 127.0.0.1 --port 8000 --workers 1 &

# Wait a bit for FastAPI to start
sleep 3

# Start nginx in foreground
nginx -g 'daemon off;'
