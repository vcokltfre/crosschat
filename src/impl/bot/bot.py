from os import getenv

from aioredis import Redis, from_url
from disnake.ext.commands import Bot as _Bot
from fakeredis.aioredis import FakeRedis
from loguru import logger

from src.impl.database import database
from src.impl.utils import SnowflakeGenerator


class Bot(_Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if not (redis_uri := getenv("REDIS_URI")):
            self.redis = FakeRedis()
        else:
            self.redis: Redis = from_url(redis_uri)

        self.sf = SnowflakeGenerator(0, 0)

    async def start(self, *args, **kwargs) -> None:
        logger.info("Connecting to the database...")

        await database.connect()

        logger.info("Connected to the database.")

        await super().start(*args, **kwargs)

    async def on_connect(self) -> None:
        logger.info("Connected to the Discord Gateway.")

    async def on_ready(self) -> None:
        logger.info(f"READY event received, connected as {self.user} with {len(self.guilds)} guilds.")

    def load_extension(self, ext: str) -> None:
        super().load_extension(ext)

        logger.info(f"Loaded extension {ext}.")
