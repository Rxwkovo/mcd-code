"""Versioned, standard-library JSON output for CLI hosts."""
from __future__ import annotations

import json
import math
import os


def envelope(command, *, data=None, messages=None, artifacts=None,
             error=None, pending=None, running=True):
    preview = None if pending is None else {
        "operation_id": pending.id, "code": pending.code, "tool": pending.tool,
        "arguments": pending.args, "summary": pending.summary,
        "expires_at": pending.expires_at,
    }
    return {
        "schema_version": 1, "ok": error is None,
        "mode": "live", "command": command,
        "data": data if data is not None else {}, "messages": messages or [],
        "artifacts": artifacts or [], "confirmation_required": preview is not None,
        "preview": preview, "error": error, "running": running,
    }


def dumps(value):
    token = os.environ.get("MCD_TOKEN")

    def clean(item):
        if isinstance(item, str):
            return item.replace(token, "[已隐藏]") if token else item
        if isinstance(item, dict):
            return {clean(str(key)): clean(entry) for key, entry in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(entry) for entry in item]
        if isinstance(item, float) and not math.isfinite(item):
            return None  # Unknown numeric values cannot become non-standard JSON NaN.
        return item

    return json.dumps(clean(value), ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def error_code(exc):
    # Public codes do not depend on exception text or upstream business wording.
    from .mcp import AuthError, RateLimitError, TransportError, MCPError
    from .safety import SafetyError
    from .service import DataError
    from .location import LocationError
    for kind, code in ((SafetyError, "CONFIRMATION_ERROR"), (AuthError, "AUTH_ERROR"),
                       (RateLimitError, "RATE_LIMITED"), (TransportError, "TRANSPORT_ERROR"),
                       (DataError, "DATA_ERROR"), (LocationError, "LOCATION_ERROR"),
                       (MCPError, "MCP_ERROR"), (OSError, "IO_ERROR")):
        if isinstance(exc, kind):
            return code
    return "INVALID_ARGUMENTS"
