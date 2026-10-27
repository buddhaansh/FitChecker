@echo off
echo Running FitChecker Test Suite...

where pytest >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    pytest tests/ -v
    pause
    exit /b
)

if exist "C:\Users\%USERNAME%\anaconda3\python.exe" (
    "C:\Users\%USERNAME%\anaconda3\python.exe" -m pytest tests/ -v
    pause
    exit /b
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/ -v
    pause
    exit /b
)

echo No Python / pytest found in standard locations.
echo Please run: pytest tests/ -v
pause
