#!/bin/bash

# LLM Translation Service Setup Script

echo "Setting up LLM Translation Service..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment configuration
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template. Please review and update as needed."
fi

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install Ollama from https://ollama.ai/"
    echo "Then run: ollama pull llama3.1:8b"
else
    echo "Ollama found. Pulling default model..."
    ollama pull llama3.1:8b
fi

# Start Redis if available
if command -v redis-server &> /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
else
    echo "Redis not found. Install Redis for caching functionality:"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
fi

echo ""
echo "Setup complete! To start the service:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start the service: python run.py"
echo "3. Access the API at: http://localhost:8888"
echo "4. View API docs at: http://localhost:8888/docs"
echo ""
echo "For demo translation, use: curl -X POST --noproxy \"*\" http://localhost:8888/api/demo/translate -F 'q=hello world'"
