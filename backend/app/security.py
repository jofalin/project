from fastapi import HTTPException, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .config import get_settings

PUBLIC_PATHS = {"/healthz", "/readiness", "/docs", "/openapi.json", "/redoc", "/health", "/api/health"}

def _extract_key(headers) -> str | None:
    direct = headers.get("x-api-key")
    if direct:
        return direct
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None

def valid_api_key(headers) -> bool:
    settings = get_settings()
    if settings.app_env.lower() not in {"production", "staging"}:
        return True
    key = _extract_key(headers)
    return bool(key and key in settings.api_keys)

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        if not valid_api_key(request.headers):
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        return await call_next(request)

async def websocket_auth(websocket: WebSocket) -> None:
    if not valid_api_key(websocket.headers):
        await websocket.close(code=4401, reason="Invalid or missing API key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
