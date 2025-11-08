#!/bin/bash

# Surgical Training Multi-Agent System - Startup Script

echo "╔═══════════════════════════════════════════════╗"
echo "║  Surgical Training Multi-Agent System         ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your DEEPSEEK_API_KEY"
    echo "Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo ""
echo "🚀 Starting the server..."
echo ""
python backend/main.py
