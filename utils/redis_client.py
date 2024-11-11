from redis import Redis as _Redis
from redis import (
    ConnectionPool,
    ConnectionError,
)
from django.conf import settings


class Redis(_Redis):

    def get_access_token(self, token: str):
        return self.get(name=f"access_token:{token}")

    def set_access_token(
        self,
        token: str,
    ):
        return self.set(
            name=f"access_token:{token}",
            value="valid",
            ex=settings.ACCESS_TOKEN_EXPIRATION_SECONDS,
        )
    
    def delete_access_token(
        self,
        token: str,
    ):
        return self.delete(f"access_token:{token}")


class RedisClient:
    _instance: Redis = None

    def __new__(cls):
        if cls._instance is None:
            try:
                cls._instance: Redis = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    connection_pool=ConnectionPool(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        max_connections=100,
                    ),
                )
                # Test connection
                cls._instance.ping()
            except ConnectionError as e:
                cls._instance = None
        return cls._instance


redis_client_ins = RedisClient()
