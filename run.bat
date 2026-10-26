@echo off
rem Start the Market Inefficiency Analyzer dashboard.
rem The first run creates the .venv environment and installs dependencies.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Setting up the environment ^(first run only^)...
    python -m venv .venv || exit /b 1
    ".venv\Scripts\python" -m pip install -r requirements.txt || exit /b 1
)

".venv\Scripts\python" -m streamlit run app.py %*
