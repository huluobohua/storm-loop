#!/bin/bash

# Kill any existing streamlit processes
pkill -f streamlit 2>/dev/null || true
sleep 2

# Set environment variables to suppress torch warnings
export TORCH_LOGS=""
export PYTORCH_DISABLE_TORCH_FUNCTION_MODE=1

# Start streamlit in the background and capture the PID
cd "$(dirname "$0")"
echo "Starting STORM frontend..."
streamlit run storm.py --server.port 8505 --server.headless true --browser.gatherUsageStats false &
STREAMLIT_PID=$!

echo "Streamlit started with PID: $STREAMLIT_PID"
echo "Frontend available at: http://localhost:8505"

# Wait a moment for startup
sleep 5

# Check if the process is still running
if kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "✅ Frontend is running successfully!"
    echo "📝 To stop: kill $STREAMLIT_PID"
else
    echo "❌ Frontend failed to start"
    exit 1
fi

# Keep the script running to show status
wait $STREAMLIT_PID