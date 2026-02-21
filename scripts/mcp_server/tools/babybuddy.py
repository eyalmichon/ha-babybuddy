"""Baby Buddy REST API tools."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import aiohttp

from mcp_server.config import get_bb_config

_SAFE_PATH = re.compile(r"^/[a-zA-Z0-9_./-]+$")


def _validate_api_path(endpoint: str) -> str:
    """Sanitize an API path to prevent SSRF / path traversal."""
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    parsed = urlparse(endpoint)
    if parsed.scheme or parsed.netloc or ".." in endpoint or "@" in endpoint:
        raise ValueError(f"Invalid API path: {endpoint}")
    if not _SAFE_PATH.match(parsed.path):
        raise ValueError(f"Invalid characters in API path: {endpoint}")
    path = parsed.path
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return path


def register(mcp) -> None:  # noqa: ANN001
    """Register all Baby Buddy tools on the given FastMCP instance."""

    @mcp.tool
    async def bb_api_get(endpoint: str) -> dict[str, Any]:
        """Call a Baby Buddy REST API endpoint (GET).

        Args:
            endpoint: API path (e.g. '/api/children/', '/api/children/test/stats/').
        """
        try:
            safe_path = _validate_api_path(endpoint)
        except ValueError as e:
            return {"error": str(e)}

        bb = get_bb_config()
        if not bb.get("api_key"):
            return {"error": "Baby Buddy API key not found in HA storage or env"}

        headers = {"Authorization": f"Token {bb['api_key']}"}
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{bb['host']}{safe_path}", headers=headers) as resp,
            ):
                body = await resp.json()
                return {"status": resp.status, "body": body}
        except (aiohttp.ClientError, OSError, TimeoutError) as e:
            return {"error": str(e)}
