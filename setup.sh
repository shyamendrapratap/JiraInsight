#!/bin/bash
# Setup script for Platform Engineering KPI Dashboard

set -e  # Exit on error

echo "=========================================="
echo "Platform Engineering KPI Dashboard Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $python_version"

# Check if version is 3.8+
required_version="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.8 or higher is required!"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✓ Python version is compatible"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data/cache
mkdir -p data/exports
mkdir -p logs
echo "✓ Directories created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your JIRA credentials:"
    echo "   - JIRA_API_TOKEN"
    echo "   - JIRA_EMAIL"
    echo "   - JIRA_URL"
    echo ""
else
    echo ".env file already exists. Skipping..."
    echo ""
fi

# Create config backup if config exists
if [ -f "config/config.yaml" ]; then
    echo "Configuration file already exists."
else
    echo "⚠️  Please configure config/config.yaml with your JIRA settings"
    echo "   See config/config.yaml for reference"
fi
echo ""

# Test installation
echo "Testing installation..."
python3 -c "import requests, yaml, dash, plotly; print('✓ All required packages are importable')"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your JIRA credentials"
echo "2. Edit config/config.yaml with your project settings"
echo "3. Test connection: python src/main.py --test-connection"
echo "4. Run dashboard: python src/main.py"
echo ""
echo "For more information, see README.md"
echo ""
