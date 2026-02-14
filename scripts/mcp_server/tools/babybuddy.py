"""Baby Buddy REST API tools."""

from __future__ import annotations

from typing import Any

import aiohttp

from mcp_server.config import get_bb_config


def register(mcp) -> None:  # noqa: ANN001
    """Register all Baby Buddy tools on the given FastMCP instance."""

    @mcp.tool
    async def bb_api_get(endpoint: str) -> dict[str, Any]:
        """Call a Baby Buddy REST API endpoint (GET).

        Args:
            endpoint: API path (e.g. '/api/children/', '/api/children/test/stats/').
        """
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        bb = get_bb_config()
        if not bb.get("api_key"):
            return {"error": "Baby Buddy API key not found in HA storage or env"}

        headers = {"Authorization": f"Token {bb['api_key']}"}
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{bb['host']}{endpoint}", headers=headers) as resp,
            ):
                body = await resp.json()
                return {"status": resp.status, "body": body}
        except (aiohttp.ClientError, OSError, TimeoutError) as e:
            return {"error": str(e)}
