"""Entry point for the Baby Buddy dev MCP server.

Run with:  PYTHONPATH=scripts python -m mcp_server
"""

from fastmcp import FastMCP

from mcp_server.tools import register_all

mcp = FastMCP("Baby Buddy Dev")
register_all(mcp)

if __name__ == "__main__":
    mcp.run()
