import json
from redis.asyncio import Redis

class RedisBus:
    def __init__(self, url: str | None, channel: str):
        self.url = url
        self.channel = channel
        self.redis: Redis | None = None

    async def connect(self) -> bool:
        if not self.url:
            return False
        self.redis = Redis.from_url(self.url, decode_responses=True)
        await self.redis.ping()
        return True

    async def close(self):
        if self.redis:
            await self.redis.aclose()
            self.redis = None

    async def available(self) -> bool:
        if not self.redis:
            return False
        try:
            return bool(await self.redis.ping())
        except Exception:
            return False

    async def publish(self, payload: dict) -> int:
        if not self.redis:
            return 0
        return await self.redis.publish(self.channel, json.dumps(payload, separators=(",", ":")))

    async def pubsub(self):
        if not self.redis:
            return None
        sub = self.redis.pubsub()
        await sub.subscribe(self.channel)
        return sub
