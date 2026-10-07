from .config import get_settings
from .redis_bus import RedisBus
from .ws_manager import WebSocketManager
from .telemetry_simulator import FallbackTelemetrySimulator

settings = get_settings()
bus = RedisBus(settings.redis_url, settings.redis_channel)
websocket_manager = WebSocketManager(bus)
simulator = FallbackTelemetrySimulator(
    stale_seconds=settings.telemetry_stale_seconds,
    on_snapshot=lambda snapshot: websocket_manager.publish({"type": "telemetry", "data": snapshot}),
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
