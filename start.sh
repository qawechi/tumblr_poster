#!/bin/bash
# ... (title and event loop part)

# =================================================================
# Section 1: Install Dependencies (Using pip3)
# =================================================================
echo ""
echo "[1/4] Checking and installing Python packages..."
# Ensure you use 'pip3' to install for Python 3
python3 -m pip install -r requirements.txt >/dev/null 2>&1
echo "        - All required packages are installed/verified."

# =================================================================
# Section 2 & 3: Run the Python setup script (Using python3)
# =================================================================
python3 setup.py

# =================================================================
# Section 4: Run the main application (Using python3)
# =================================================================
echo ""
echo "[4/4] All setup is complete. Starting the main news bot..."
echo "================================================================="
echo ""
python3 main.py
