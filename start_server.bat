@echo off
echo =======================================
echo Ensuring uv Virtual Environment exists...
echo =======================================
if not exist ".venv" (
    uv venv
)

echo.
echo =======================================
echo Installing Dependencies with uv...
echo =======================================
uv pip install -r requirements.txt

echo.
echo =======================================
echo Starting AgriCore MCP Server...
echo =======================================
uv run python main.py

pause
