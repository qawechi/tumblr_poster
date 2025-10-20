@ECHO OFF
TITLE "News Bot ONE-TIME Setup"
CLS

ECHO.
ECHO  ======================================================
ECHO   Welcome to the Nozhin News Bot Interactive Setup
ECHO  ======================================================
ECHO.
ECHO  This script will guide you through configuring your
ECHO  .env file with the necessary API keys and settings.
ECHO.

ECHO [1/2] Installing Python dependencies...
pip install -r requirements.txt --quiet
ECHO      - Dependencies installed.

ECHO.
ECHO [2/2] Running interactive configuration for .env file...
python setup.py

ECHO.
ECHO  ======================================================
ECHO   Setup is complete!
ECHO  ======================================================
ECHO.
ECHO  - Your settings are saved in the '.env' file.
ECHO  - You can now run the bot using 'start.bat'.
ECHO.
PAUSE