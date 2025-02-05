#!/bin/bash


# Infinite loop to restart the script if it exits
while true; do
    echo "Starting media_server.py..."
    python3 /Users/kr/Projects/media_server/qb_api.py
    echo "media_server.py exited. Restarting in 5 seconds..."
    sleep 30
done