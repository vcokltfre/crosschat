from os import getenv

from aioredis import Redis, from_url
from cachingutils import acached, cached
from disnake.ext.commands import Bot as _Bot
from fakeredis.aioredis import FakeRedis
from loguru import logger
from ormar import NoMatch

from src.impl.core import ChannelManager
from src.impl.database import Channel, User, database


class Bot(_Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if not (redis_uri := getenv("REDIS_URI")):
            self.redis = FakeRedis()
        else:
            self.redis: Redis = from_url(redis_uri)

        self.vchannels: dict[str, ChannelManager] = {}
        self.ccache: dict[int, ChannelManager] = {}
        self.vusers: dict[int, User] = {}

    @acached(timeout=30)
    async def resolve_user(self, user_id: int, user_name: str) -> User:
        user = self.vusers.get(user_id)

        if user is None:
            try:
                user = await User.objects.first(id=user_id)
            except NoMatch:
                user = await User(id=user_id, name=str(user_name)).save()

            self.vusers[user.id] = user

        return user

    @cached(timeout=10)
    def resolve_channel(self, channel_id: int) -> ChannelManager | None:
        channel = self.ccache.get(channel_id, None)

        if channel:
            return channel

        for channel in self.vchannels.values():
            if channel.handles(channel_id):
                self.ccache[channel_id] = channel
                return channel

    async def start(self, *args, **kwargs) -> None:
        logger.info("Connecting to the database...")

        await database.connect()

        logger.info("Connected to the database.")

        channels = await Channel.objects.all()

        for channel in channels:
            self.vchannels[channel.name] = ChannelManager(self, channel)

            await self.vchannels[channel.name].setup()

        await super().start(*args, **kwargs)

    async def on_connect(self) -> None:
        logger.info("Connected to the Discord Gateway.")

    async def on_ready(self) -> None:
        logger.info(f"READY event received, connected as {self.user} with {len(self.guilds)} guilds.")

    def load_extension(self, ext: str) -> None:
        super().load_extension(ext)

        logger.info(f"Loaded extension {ext}.")
