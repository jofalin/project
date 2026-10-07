import asyncio
import random
from datetime import datetime, timezone

class FallbackTelemetrySimulator:
    def __init__(self, stale_seconds: int = 10, on_snapshot=None):
        self.stale_seconds = stale_seconds
        self.on_snapshot = on_snapshot
        self.running = False
        self.task = None
        self.last_live: dict[str, float] = {}
        self.occupancy = {f"zone-{i:03d}": random.randint(100, 500) for i in range(1, 9)}

    def mark_live(self, zone_id: str):
        self.last_live[zone_id] = asyncio.get_running_loop().time()

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None

    async def _loop(self):
        while self.running:
            await asyncio.sleep(2)
            now_mono = asyncio.get_running_loop().time()
            for zone_id, value in self.occupancy.items():
                if now_mono - self.last_live.get(zone_id, 0) < self.stale_seconds:
                    continue
                self.occupancy[zone_id] = max(0, value + random.randint(-12, 18))
                snapshot = {
                    "zone_id": zone_id,
                    "occupancy": self.occupancy[zone_id],
                    "inflow_rate": max(0, 20 + random.uniform(-5, 15)),
                    "outflow_rate": max(0, 18 + random.uniform(-5, 15)),
                    "density_ratio": min(1.0, self.occupancy[zone_id] / 1000.0),
                    "weather_severity": 0.1,
                    "source": "synthetic-fallback",
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                }
                if self.on_snapshot:
                    await self.on_snapshot(snapshot)
