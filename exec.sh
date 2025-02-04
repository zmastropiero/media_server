#!/bin/bash

# Activate the virtual environment
source ~/Projects/media_server/venv/bin/activate

# Infinite loop to restart the script if it exits
while true; do
    echo "Starting media_server.py..."
    python3 ~/Projects/media_server/src/media_server.py
    echo "media_server.py exited. Restarting in 5 seconds..."
    sleep 30
done