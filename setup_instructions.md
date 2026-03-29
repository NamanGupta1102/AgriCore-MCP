# Environment Setup & Running

This guide explains how to start the AgriCore MCP Server locally using `uv`—an extremely fast Python package installer and resolver. 

A python virtual environment (`.venv`) is used in the project root to ensure dependencies (`mcp`, `json-logic-py`, etc.) are installed in isolation, preventing conflicts with your global python settings.

## Getting Started

To launch the server automatically:
1. Double click or run **`start_server.bat`** from the terminal in the workspace root.
   - This script will automatically create a `.venv` virtual environment using `uv venv` if it doesn't exist.
   - It will install all dependencies extremely fast from `requirements.txt` using `uv pip`.
   - It will start the server using standard stdio mode via `uv run`.

### Manual Launch
If you prefer to start it manually from a PowerShell/CMD terminal, ensure you have `uv` installed, then run:

1. **Create the environment:**
   ```powershell
   uv venv
   ```
2. **Install requirements:**
   ```powershell
   uv pip install -r requirements.txt
   ```
3. **Run the server:**
   ```powershell
   uv run python src/server_main.py
   ```
