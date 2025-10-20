@ECHO OFF
TITLE "Nozhin News Bot Runner"
CLS

:: Set event loop policy for stable asyncio on Windows (Python 3.8+)
SET ASYCIO_EVENT_LOOP_POLICY=asyncio.WindowsSelectorEventLoopPolicy

ECHO  ======================================================
ECHO   Starting the Nozhin News Bot...
ECHO  ======================================================
ECHO.
ECHO  - The bot is now running.
ECHO  - It will fetch, translate, and post articles in cycles.
ECHO  - Press CTRL+C in this window to stop the bot.
ECHO.
ECHO  ======================================================
ECHO.

python main.py