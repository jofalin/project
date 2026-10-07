from .config import get_settings
from .redis_bus import RedisBus
from .ws_manager import WebSocketManager
from .telemetry_simulator import FallbackTelemetrySimulator

settings = get_settings()
bus = RedisBus(settings.redis_url, settings.redis_channel)
websocket_manager = WebSocketManager(bus)

async def _handle_simulated_snapshot(snapshot: dict):
    if settings.database_url:
        try:
            from .production_db import get_session_factory
            from .production_models import TelemetrySnapshot
            from datetime import datetime
            async with get_session_factory() as session:
                session.add(TelemetrySnapshot(
                    captured_at=datetime.fromisoformat(snapshot["captured_at"]),
                    zone_id=snapshot["zone_id"],
                    occupancy=snapshot["occupancy"],
                    inflow_rate=snapshot["inflow_rate"],
                    outflow_rate=snapshot["outflow_rate"],
                    density_ratio=snapshot["density_ratio"],
                    weather_severity=snapshot["weather_severity"],
                    source=snapshot["source"],
                ))
                await session.commit()
        except Exception:
            pass
    await websocket_manager.publish({"type": "telemetry", "data": snapshot})

simulator = FallbackTelemetrySimulator(
    stale_seconds=settings.telemetry_stale_seconds,
    on_snapshot=_handle_simulated_snapshot,
)

async def start_runtime():
    try:
        await bus.connect()
    except Exception:
        pass
    await websocket_manager.start()
    await simulator.start()

async def stop_runtime():
    await simulator.stop()
    await websocket_manager.stop()
    await bus.close()
