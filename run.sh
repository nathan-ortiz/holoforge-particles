#!/bin/bash
# HoloForge Particles launcher
# Optimized for Raspberry Pi 5 + HyperPixel 4.0 Square display

set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set display for HyperPixel
export DISPLAY=:0.0
export SDL_VIDEODRIVER=x11

# Disable SDL audio (not needed for visual display)
export SDL_AUDIODRIVER=dummy

# Performance optimizations for Pi 5
export PYGAME_HIDE_SUPPORT_PROMPT=1

echo "Starting HoloForge Particles..."
echo ""

# Run application
python main.py

echo ""
echo "HoloForge Particles terminated."
