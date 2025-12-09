#!/bin/bash

# Start the Integrated Network Platform
# Port: 11100 (Safe range)

echo "Starting Integrated Network Platform on port 11100..."

# Ensure dependencies
if ! python3 -c "import uvicorn" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip install meraki mac-vendor-lookup
fi

# Run Server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 11100 --reload
