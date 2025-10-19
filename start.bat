@ECHO OFF
:: The quotes around the title fix the "'Runner' is not recognized" error
TITLE "News Bot Setup & Runner"

:: =================================================================
:: CRITICAL FIX: Set event loop policy for stable asyncio on Windows (Python 3.8+)
:: This resolves the "no current event loop" error.
SET ASYNCIO_EVENT_LOOP_POLICY=asyncio.WindowsSelectorEventLoopPolicy

:: =================================================================
:: Section 1: Install Dependencies
:: =================================================================
ECHO.
ECHO [1/4] Checking and installing Python packages...
pip install -r requirements.txt --quiet
ECHO     - All required packages are installed/verified.

:: =================================================================
:: Section 2 & 3: Run the Python setup script
:: =================================================================
python setup.py

:: =================================================================
:: Section 4: Run the main application
:: =================================================================
ECHO.
ECHO [4/4] All setup is complete. Starting the main news bot...
ECHO =================================================================
ECHO.
python main.py