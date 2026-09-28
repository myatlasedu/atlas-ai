import redis.asyncio as redis

from core.config import settings

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )

    async def close(self):
        await self.redis_client.close()

redis_client = RedisClient()