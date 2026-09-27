from cache.redis import redis_client


class RedisCache:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def get_redis_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def set(self, key, value, expire=None):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.set(
            key,
            value,
            ex=expire,
        )

    async def set_if_not_exists(
        self,
        key,
        value,
        expire=None,
    ):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.set(
            key,
            value,
            ex=expire,
            nx=True,
        )

    async def get(self, key):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.get(
            key
        )

    async def delete(self, key):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.delete(
            key
        )

    async def exists(self, key):
        key = self.get_redis_key(key)

        return (
            await redis_client.redis_client.exists(
                key
            )
        ) > 0

    async def lpush(self, key, value):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.lpush(
            key,
            value,
        )

    async def rpush(self, key, *values):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.rpush(
            key,
            *values,
        )

    async def ltrim(self, key, start, end):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.ltrim(
            key,
            start,
            end,
        )

    async def lrange(self, key, start, end):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.lrange(
            key,
            start,
            end,
        )

    async def expire(self, key, seconds):
        key = self.get_redis_key(key)

        return await redis_client.redis_client.expire(
            key,
            seconds,
        )

    async def delete_if_value_matches(
        self,
        key,
        value,
    ):
        """
        Atomically delete the key only if its current
        value matches the expected value.
        """

        key = self.get_redis_key(key)

        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        return await redis_client.redis_client.eval(
            script,
            1,
            key,
            value,
        )

    async def append_list_with_ttl(
        self,
        key: str,
        value,
        max_items: int,
        expire: int,
    ):
        key = self.get_redis_key(key)

        pipe = redis_client.redis_client.pipeline(
            transaction=True
        )

        pipe.lpush(
            key,
            value,
        )

        pipe.ltrim(
            key,
            0,
            max_items - 1,
        )

        pipe.expire(
            key,
            expire,
        )

        return await pipe.execute()


    async def replace_list_with_ttl(
        self,
        key: str,
        values: list,
        expire: int,
    ):
        key = self.get_redis_key(key)

        pipe = redis_client.redis_client.pipeline(
            transaction=True
        )

        pipe.delete(key)

        if values:
            pipe.rpush(
                key,
                *values,
            )

            pipe.expire(
                key,
                expire,
            )

        return await pipe.execute()