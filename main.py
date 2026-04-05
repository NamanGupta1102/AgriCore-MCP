"""
Railway / production entry point.

Ensures `src/` is on sys.path, then starts the FastMCP server in SSE (HTTP) mode
on 0.0.0.0 using the PORT environment variable (default 8000). Configure via
server_main (BIND_HOST, PORT).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from server_main import main  # noqa: E402

if __name__ == "__main__":
    main()
