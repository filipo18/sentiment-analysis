"""Client integration for Gate22 MCP endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("app.aci_mcp_client")


class Gate22MCPClient:
    """Thin HTTP client for interacting with Gate22 MCP endpoints."""

    def __init__(self, base_url: str, token: Optional[str] = None, *, timeout: float = 30.0, max_retries: int = 3) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = httpx.Timeout(timeout, connect=10.0)
        self.max_retries = max(1, max_retries)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _post(self, function: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{function}"
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=self._headers())
                    response.raise_for_status()
                    data = response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                logger.warning("Gate22 MCP %s attempt %s failed: %s", function, attempt, exc)
                continue
            except ValueError as exc:  # JSON decode error
                last_exc = exc
                logger.warning("Gate22 MCP %s attempt %s returned invalid JSON: %s", function, attempt, exc)
                continue

            if isinstance(data, dict):
                if data.get("error"):
                    message = data.get("error")
                    raise RuntimeError(f"Gate22 MCP error: {message}")
                if data.get("errors"):
                    raise RuntimeError(f"Gate22 MCP errors: {data['errors']}")
                return data

            logger.warning("Gate22 MCP %s attempt %s returned non-dict payload", function, attempt)
            last_exc = RuntimeError("Invalid MCP response shape")

        raise RuntimeError(f"Failed to call Gate22 MCP {function}: {last_exc}")

    def search_tools(self, q: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"query": q or ""}
        return self._post("search", payload)

    def execute(self, tool: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"tool": tool, "action": action, "params": params}
        return self._post("execute", payload)
