@ECHO OFF
TITLE News Bot Setup & Runner

:: =================================================================
:: Section 1: Check for Python Dependencies
:: =================================================================
ECHO.
ECHO [1/5] Checking for required Python packages...

:: Create a temporary flag file
DEL installed_flag.tmp 2>nul

:: Check if all packages in requirements.txt are installed
pip freeze > installed_packages.tmp
fc installed_packages.tmp requirements.txt >nul
IF %ERRORLEVEL%==0 (
    ECHO      - All packages are already installed.
    GOTO Configure
)

:: If check failed, try a more robust line-by-line check
FOR /F "delims==" %%p IN (requirements.txt) DO (
    pip show %%p >nul 2>nul
    IF ERRORLEVEL 1 (
        ECHO      - Missing package found. Proceeding to installation.
        GOTO InstallDependencies
    )
)

ECHO      - All packages are already installed.
DEL installed_packages.tmp 2>nul
GOTO Configure

:InstallDependencies
ECHO.
ECHO [2/5] Installing dependencies from requirements.txt...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    ECHO.
    ECHO ERROR: Installation failed. Please check your internet connection and pip setup.
    PAUSE
    EXIT
)
ECHO      - Installation complete.
DEL installed_packages.tmp 2>nul

:: =================================================================
:: Section 2: Configure the .env file
:: =================================================================
:Configure
ECHO.
ECHO [3/5] Please enter your configuration details.
ECHO.

SET /P NEWS_API_KEY="Enter your NewsAPI Key: "
SET /P GEMINI_API_KEY="Enter your Google Gemini API Key: "
SET /P TUMBLR_CONSUMER_KEY="Enter your Tumblr Consumer Key: "
SET /P TUMBLR_CONSUMER_SECRET="Enter your Tumblr Consumer Secret: "
SET /P TUMBLR_BLOG_NAME="Enter your Tumblr Blog Name (e.g., qawechi): "

ECHO.
ECHO      - Saving configuration to .env file...

:: Overwrite the .env file with the new configuration
(
    ECHO # NewsAPI.org Key
    ECHO NEWS_API_KEY="%NEWS_API_KEY%"
    ECHO.
    ECHO # Google Gemini API Key
    ECHO GEMINI_API_KEY="%GEMINI_API_KEY%"
    ECHO.
    ECHO # Tumblr API Keys
    ECHO TUMBLR_CONSUMER_KEY="%TUMBLR_CONSUMER_KEY%"
    ECHO TUMBLR_CONSUMER_SECRET="%TUMBLR_CONSUMER_SECRET%"
    ECHO TUMBLR_BLOG_NAME="%TUMBLR_BLOG_NAME%"
) > .env

ECHO      - Configuration saved.

:: =================================================================
:: Section 3: Run the Tumblr Token Generator
:: =================================================================
ECHO.
ECHO [4/5] Running the Tumblr token generation script...
ECHO      - Please follow the on-screen instructions to authorize the app.
ECHO.
python get_token.py

ECHO.
ECHO      - Token generation process finished.
ECHO.
ECHO The script has printed your OAuth Token and Secret above.
ECHO Please copy and paste them here to save them to your .env file.
ECHO.

SET /P TUMBLR_OAUTH_TOKEN="Paste the TUMBLR_OAUTH_TOKEN here: "
SET /P TUMBLR_OAUTH_SECRET="Paste the TUMBLR_OAUTH_SECRET here: "

ECHO.
ECHO      - Appending the final OAUTH tokens to your .env file...

:: Append the user-provided tokens to the .env file
(
    ECHO.
    ECHO # Tumblr OAuth Tokens (retrieved from get_token.py)
    ECHO TUMBLR_OAUTH_TOKEN="%TUMBLR_OAUTH_TOKEN%"
    ECHO TUMBLR_OAUTH_SECRET="%TUMBLR_OAUTH_SECRET%"
) >> .env

ECHO      - Tokens saved.

:: =================================================================
:: Section 4: Run the main application
:: =================================================================
ECHO.
ECHO [5/5] All setup is complete. Starting the main news bot...
ECHO =================================================================
ECHO.
python main.py

ECHO.
ECHO =================================================================
ECHO Script has finished running. Press any key to exit.
PAUSE >nul