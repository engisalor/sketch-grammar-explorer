"""Hooks for processing Responses."""
import json
import logging
import time

from requests import Response


def wait(n_calls: int, server_info: dict) -> int:
    """Returns a server's required wait time for a given number of calls."""
    if not server_info.get("wait"):
        return 0
    else:
        waits = []
        for k, v in server_info["wait"].items():
            if v:
                if n_calls <= v:
                    waits.append(float(k))
        if not waits:
            waits.append(max([float(k) for k in server_info["wait"].keys()]))
        return min(waits)


def wait_hook(timeout: float = 1.0):
    """Hook to control wait periods between non-cached calls."""

    def _wait(response, *args, **kwargs):
        if not getattr(response, "from_cache", False):
            if timeout:
                logging.info(f"...waiting {timeout}")
            time.sleep(timeout)
        return response

    return _wait


def redact_json(response: Response) -> Response:
    """Removes credentials from JSON Response data."""
    data = response.json()
    if data.get("request"):
        data["request"].pop("username", None)
        data["request"].pop("api_key", None)
    response.__dict__["_content"] = json.dumps(data).encode("utf-8")
    return response


def redact_hook():
    """Hook for redacting Response content."""

    def _redact(response, *args, **kwargs):
        if not getattr(response, "from_cache", False):
            if "application/json" in response.headers.get("Content-Type"):
                return redact_json(response)

    return _redact
