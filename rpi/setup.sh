#!/usr/bin/env bash
# Setup script for UGV01 RPi control server.
# Run once on a fresh Raspberry Pi 5.

set -e

echo "=== UGV01 RPi Setup ==="

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Add user to dialout group for serial port access
if ! groups | grep -q dialout; then
    sudo usermod -aG dialout "$USER"
    echo "Added $USER to dialout group. Log out and back in for this to take effect."
fi

echo ""
echo "=== Setup complete ==="
echo "To run:"
echo "  source venv/bin/activate"
echo "  python main.py --port /dev/ttyUSB0"
echo ""
echo "If using GPIO UART instead of USB:"
echo "  python main.py --port /dev/ttyAMA0"
