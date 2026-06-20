@echo off
setlocal

set "TRAINER_DIR=%~dp0"
set "PYTHONPATH=%TRAINER_DIR%src;%PYTHONPATH%"

cd /d "%TRAINER_DIR%"

where python >nul 2>nul
if errorlevel 1 (
    echo Python wurde nicht gefunden. Bitte Python 3.12 oder neuer installieren.
    pause
    exit /b 1
)

python -m mcs_trainer gui %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Trainer-GUI konnte nicht gestartet werden.
    echo Falls Abhaengigkeiten fehlen, im Ordner trainer ausfuehren:
    echo python -m pip install -e ".[gui,ml]"
    echo.
    pause
)

exit /b %EXIT_CODE%
