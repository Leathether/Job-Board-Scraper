#!/bin/bash

echo "Starting LinkedIn Job Scraper Backend Server..."

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    echo "Error: server.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3."
    exit 1
fi

# Remove existing venv if it's corrupted
if [ -d "venv" ] && [ ! -f "venv/bin/python" ]; then
    echo "Removing corrupted virtual environment..."
    rm -rf venv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
. venv/bin/activate

# Install requirements
echo "Installing Python requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements."
    exit 1
fi

# Check if Chrome/Chromium is installed
if ! command -v chromium-browser &> /dev/null && ! command -v google-chrome &> /dev/null; then
    echo "Warning: Chrome/Chromium not found. Installing Chromium..."
    sudo apt update && sudo apt install -y chromium-browser chromium-chromedriver
fi

# Start the server
echo "Starting FastAPI server on port 8000..."
python server.py 