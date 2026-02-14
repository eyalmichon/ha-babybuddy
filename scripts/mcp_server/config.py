"""Shared configuration for the MCP dev server.

Secrets (HA refresh token, BB API key) are read from HA's local
.storage/ files at runtime — never hardcoded or committed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

HA_URL = os.environ.get("HA_URL", "http://localhost:8123")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/workspaces/ha-babybuddy")

_HA_STORAGE = Path(PROJECT_ROOT) / ".dev" / "ha" / ".storage"


def get_ha_refresh_token() -> str | None:
    """Read the HA refresh token from local .storage/auth.

    Finds the token with client_id matching HA_URL.
    Falls back to HA_REFRESH_TOKEN env var if storage is unavailable.
    """
    env = os.environ.get("HA_REFRESH_TOKEN")
    try:
        data = json.loads((_HA_STORAGE / "auth").read_text())
        client_id = f"{HA_URL}/"
        for token in data["data"].get("refresh_tokens", []):
            if token.get("client_id") == client_id:
                return token["token"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    return env


def get_bb_config() -> dict[str, Any]:
    """Read Baby Buddy connection details from HA's config entries.

    Returns dict with 'host', 'port', and 'api_key'.
    Falls back to BB_HOST / BB_API_KEY env vars if storage is unavailable.
    """
    fallback = {
        "host": os.environ.get("BB_HOST", ""),
        "port": int(os.environ.get("BB_PORT", "8000")),
        "api_key": os.environ.get("BB_API_KEY", ""),
    }
    try:
        data = json.loads((_HA_STORAGE / "core.config_entries").read_text())
        for entry in data["data"]["entries"]:
            if entry.get("domain") == "babybuddy":
                d = entry["data"]
                return {
                    "host": f"{d['host']}:{d['port']}{d.get('path') or ''}",
                    "port": d["port"],
                    "api_key": d["api_key"],
                }
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    return fallback
