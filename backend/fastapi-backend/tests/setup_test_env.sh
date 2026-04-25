#!/bin/bash
# Setup script for test environment

set -e

echo "Setting up test environment for eClinic Backend..."

# Check if python3-venv is installed
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "ERROR: python3-venv is not installed."
    echo ""
    echo "Please install it using one of the following methods:"
    echo ""
    echo "Option 1 (Recommended - requires sudo):"
    echo "  sudo apt update && sudo apt install -y python3.12-venv"
    echo ""
    echo "Option 2 (If you have pipx):"
    echo "  pipx install pytest"
    echo ""
    echo "Option 3 (Use system packages with --break-system-packages):"
    echo "  python3 -m pip install --break-system-packages -r requirements.txt"
    echo ""
    exit 1
fi

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import fastapi; print('✓ FastAPI installed')"
python -c "import pytest; print('✓ pytest installed')"
python -c "import sqlalchemy; print('✓ SQLAlchemy installed')"

echo ""
echo "✓ Test environment setup complete!"
echo ""
echo "To run tests, activate the virtual environment first:"
echo "  source venv/bin/activate"
echo ""
echo "Then run pytest:"
echo "  pytest"
echo ""
