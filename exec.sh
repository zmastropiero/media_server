#!/bin/bash


# Infinite loop to restart the script if it exits
while true; do
    echo "Starting qb_api.py..."
    python3 qb_api.py
    echo "qb_api.py exited. Restarting in 6 seconds..."
    sleep 60
done