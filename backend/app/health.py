from .config import get_settings
from .production_db import check_database
from .runtime import bus

MODEL_INITIALIZED = True

async def health_snapshot() -> dict:
    settings = get_settings()
    db_ok = await check_database() if settings.database_url else False
    redis_ok = await bus.available()
    fully_ready = bool(db_ok and MODEL_INITIALIZED and (redis_ok if settings.redis_url else True))
    return {
        "status": "ok" if fully_ready else "degraded",
        "database": {"configured": bool(settings.database_url), "ok": db_ok},
        "redis": {"configured": bool(settings.redis_url), "ok": redis_ok},
        "model": {"initialized": MODEL_INITIALIZED},
    }
