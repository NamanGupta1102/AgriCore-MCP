@echo off
echo =======================================
echo Syncing uv environment (uv.lock)...
echo =======================================
uv sync

echo.
echo =======================================
echo Starting AgriCore MCP Server...
echo =======================================
uv run python main.py

pause
