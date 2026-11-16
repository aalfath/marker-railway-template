"""Marker's FastAPI server and viewer behind an API key.

The key (MARKER_API_KEY) is accepted as:
  * Authorization: Bearer <key>
  * X-API-Key: <key>
  * HTTP basic auth with any user name and the key as password (browsers)
/health stays open for Railway's health check.
"""
import base64
import hmac
import os
import socket

import uvicorn
from starlette.responses import PlainTextResponse

from marker.scripts.server import app

API_KEY = os.environ.get("MARKER_API_KEY", "")
OPEN_PATHS = {"/health"}


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


def _presented_key(headers) -> str | None:
    key = headers.get("x-api-key")
    if key:
        return key.strip()
    scheme, _, value = headers.get("authorization", "").partition(" ")
    scheme = scheme.lower()
    if scheme == "bearer":
        return value.strip()
    if scheme == "basic":
        try:
            return base64.b64decode(value.strip()).decode("utf-8").partition(":")[2]
        except Exception:
            return None
    return None


@app.middleware("http")
async def require_api_key(request, call_next):
    if not API_KEY or request.url.path in OPEN_PATHS:
        return await call_next(request)
    key = _presented_key(request.headers)
    if key is not None and hmac.compare_digest(key.encode(), API_KEY.encode()):
        return await call_next(request)
    return PlainTextResponse(
        "Unauthorized: send the MARKER_API_KEY as a Bearer token, an X-API-Key header, or the basic-auth password.",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Marker", charset="UTF-8"'},
    )


def _listen_socket(port: int) -> socket.socket:
    """Dual-stack listener: Railway's health check uses IPv4 and its private
    network uses IPv6. uvicorn's own "::" bind goes through asyncio, which sets
    IPV6_V6ONLY, so bind the socket here with it switched off."""
    host = os.environ.get("HOST")
    if not host:
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            sock.bind(("::", port))
            return sock
        except OSError:
            host = "0.0.0.0"
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    sock = _listen_socket(port)
    print(
        f"Marker server listening on {sock.getsockname()[0]} port {port}"
        f" (threads: {os.environ.get('OMP_NUM_THREADS')})",
        flush=True,
    )
    config = uvicorn.Config(app, proxy_headers=True, forwarded_allow_ips="*")
    uvicorn.Server(config).run(sockets=[sock])
