import redis.asyncio as aioredis
from app.config import settings

redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return redis_pool


async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None


async def cache_get(key: str) -> str | None:
    r = await get_redis()
    return await r.get(key)


async def cache_set(key: str, value: str, ttl: int = 60):
    r = await get_redis()
    await r.setex(key, ttl, value)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


async def cache_mget(keys: list[str]) -> list[str | None]:
    r = await get_redis()
    return await r.mget(keys)


async def cache_mset(data: dict[str, str], ttl: int = 60):
    r = await get_redis()
    pipe = r.pipeline()
    for key, value in data.items():
        pipe.setex(key, ttl, value)
    await pipe.execute()
