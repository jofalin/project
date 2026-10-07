import asyncio
import json
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from .redis_bus import RedisBus
from .security import websocket_auth

class WebSocketManager:
    def __init__(self, bus: RedisBus):
        self.bus = bus
        self.connections: dict[WebSocket, float] = {}
        self._redis_task = None
        self._heartbeat_task = None

    async def start(self):
        if await self.bus.available():
            self._redis_task = asyncio.create_task(self._redis_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        for task in (self._redis_task, self._heartbeat_task):
            if task:
                task.cancel()
        for websocket in list(self.connections):
            try:
                await websocket.close()
            except Exception:
                pass
        self.connections.clear()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections[websocket] = asyncio.get_running_loop().time()

    async def disconnect(self, websocket: WebSocket):
        self.connections.pop(websocket, None)

    async def broadcast_local(self, payload: dict):
        dead = []
        for websocket in list(self.connections):
            try:
                await websocket.send_text(json.dumps(payload, separators=(",", ":")))
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            await self.disconnect(websocket)

    async def publish(self, payload: dict):
        count = await self.bus.publish(payload)
        if count == 0:
            await self.broadcast_local(payload)

    async def _redis_loop(self):
        sub = await self.bus.pubsub()
        if not sub:
            return
        try:
            async for message in sub.listen():
                if message.get("type") == "message":
                    await self.broadcast_local(json.loads(message["data"]))
        finally:
            await sub.close()

    async def _heartbeat_loop(self):
        while True:
            await asyncio.sleep(15)
            now = asyncio.get_running_loop().time()
            for websocket, last_pong in list(self.connections.items()):
                if now - last_pong > 45:
                    await self.disconnect(websocket)
                    try:
                        await websocket.close(code=1011, reason="heartbeat timeout")
                    except Exception:
                        pass
                    continue
                try:
                    await websocket.send_json({"type": "ping", "ts": datetime.now(timezone.utc).isoformat()})
                except Exception:
                    await self.disconnect(websocket)

    async def handle(self, websocket: WebSocket):
        await websocket_auth(websocket)
        await self.connect(websocket)
        try:
            while True:
                data = json.loads(await websocket.receive_text())
                if data.get("type") == "pong":
                    self.connections[websocket] = asyncio.get_running_loop().time()
        except (WebSocketDisconnect, json.JSONDecodeError):
            await self.disconnect(websocket)
