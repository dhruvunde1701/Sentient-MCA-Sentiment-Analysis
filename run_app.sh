#!/bin/bash

# E-Consultation Sentiment Analysis MVP Startup Script
echo "Starting E-Consultation Sentiment Analysis System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and run the app
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Launching Streamlit application..."
    echo "The application will open in your browser at http://localhost:8501"
    echo "Press Ctrl+C to stop the application"
    echo ""

    streamlit run app.py
else
    echo "❌ Virtual environment activation script not found!"
    exit 1
fi
