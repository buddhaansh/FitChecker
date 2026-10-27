@echo off
echo Starting FitChecker...
echo Checking for Python environment...

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -m streamlit run app.py
    pause
    exit /b
)

if exist "C:\Users\%USERNAME%\anaconda3\python.exe" (
    "C:\Users\%USERNAME%\anaconda3\python.exe" -m streamlit run app.py
    pause
    exit /b
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
    pause
    exit /b
)

echo No Python executable found in standard locations.
echo Please run: streamlit run app.py
pause
