#!/bin/bash

# =================================================================
# Title: Set the terminal window title
# The 'echo -ne' part is a common way to set the title in many terminals
# =================================================================
echo -ne "\033]0;News Bot Setup & Runner\007"

# =================================================================
# CRITICAL FIX: Set event loop policy for stable asyncio on Windows (Python 3.8+)
# This is a Windows-specific fix and is usually NOT needed or is
# counterproductive on Linux/macOS. It has been commented out.
# On Unix-like systems, the default event loop (ProactorEventLoop) is typically fine.
# export ASYNCIO_EVENT_LOOP_POLICY=asyncio.WindowsSelectorEventLoopPolicy
# =================================================================

# =================================================================
# Section 1: Install Dependencies
# =================================================================
echo ""
echo "[1/4] Checking and installing Python packages..."
# Using '>/dev/null 2>&1' for quiet output, similar to '--quiet'
pip install -r requirements.txt >/dev/null 2>&1
echo "        - All required packages are installed/verified."

# =================================================================
# Section 2 & 3: Run the Python setup script
# =================================================================
python3 setup.py

# =================================================================
# Section 4: Run the main application
# =================================================================
echo ""
echo "[4/4] All setup is complete. Starting the main news bot..."
echo "================================================================="
echo ""
python main.py
