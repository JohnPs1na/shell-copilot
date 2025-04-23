#!/bin/bash
# run_project.sh

source env.sh

# Check if Temporal server is running
if ! pgrep -f "temporal server" > /dev/null; then
    echo "Starting Temporal server..."
    temporal server start-dev &
    sleep 1
else
    echo "Temporal server is already running"
fi

# Check if bugs_daemon is running
if ! pgrep -f "bugs_daemon" > /dev/null; then
    echo "Starting bugs_daemon..."
    python bugs_daemon.py &
    sleep 1
else
    echo "bugs_daemon is already running"
fi

# Check if Python worker is running
if ! pgrep -f "run_worker.py" > /dev/null; then
    echo "Starting Python worker..."
    python temporal_stuff/run_worker.py &
    sleep 1
else
    echo "Python worker is already running"
fi

# Check if server.py is running on port 12345
if ! lsof -i :12345 > /dev/null 2>&1; then
    echo "Starting server.py..."
    python server.py &
    sleep 1
else
    echo "server.py is already running on port 12345"
fi

