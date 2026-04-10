#!/bin/bash
# Start Command Center Dashboard and Backend
# Run this from the project root directory

echo "🚀 Starting Steganography Command Center..."
echo ""

# Check if we're in the right directory
if [ ! -d "Frontend" ]; then
    echo "❌ Error: Frontend directory not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "📦 Backend on port 5000"
echo "🎨 Frontend on port 3000"
echo ""

# Start Backend in background
echo "Starting backend server..."
python -m uvicorn app:app --host 127.0.0.1 --port 5000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Frontend dev server
echo "Starting frontend server..."
cd Frontend
npm run dev

# Kill backend when frontend exits
kill $BACKEND_PID 2>/dev/null

echo ""
echo "Services stopped."
