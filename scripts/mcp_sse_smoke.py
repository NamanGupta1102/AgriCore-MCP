"""
Local MCP smoke test over HTTP/SSE: initialize, list tools, list resources.

Usage:
  uv run python scripts/mcp_sse_smoke.py http://127.0.0.1:8765/sse
"""
from __future__ import annotations

import asyncio
import sys

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


async def main(url: str) -> None:
    async with sse_client(url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", sorted(t.name for t in tools.tools))
            resources = await session.list_resources()
            print("resources:", sorted(r.uri for r in resources.resources))


if __name__ == "__main__":
    sse_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/sse"
    asyncio.run(main(sse_url))
