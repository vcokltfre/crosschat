from disnake import Message
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from loguru import logger

from src import Bot
from src.impl.database import Channel, ChannelMap

from ..control.admin import Admin


class Listener(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.mapping: dict[int, Channel] = {}
        self.backmap: dict[int, list[int]] = {}

        self.cache_loop.start()

    @Cog.listener()
    async def on_channel_mapped(self, cmap: ChannelMap) -> None:
        self.mapping[cmap.channel_id] = cmap.channel
        if cmap.channel.id not in self.backmap:
            self.backmap[cmap.channel.id] = []
        self.backmap[cmap.channel.id].append(cmap.channel_id)

        logger.info(f"Updated channel mapping info for {cmap.channel_id} -> {cmap.channel.id}")

    @Cog.listener()
    async def on_channel_unmapped(self, cmap: ChannelMap) -> None:
        self.mapping.pop(cmap.channel_id, None)
        self.backmap[cmap.channel.id].remove(cmap.channel_id)

        logger.info(f"Removed channel mapping info for {cmap.channel_id}")

    @loop(minutes=1)
    async def cache_loop(self) -> None:
        await self.bot.wait_until_ready()

        cmaps = await ChannelMap.objects.all()

        self.mapping = {}
        self.backmap = {}

        for mapping in cmaps:
            self.mapping[mapping.channel_id] = mapping.channel
            if mapping.channel.id not in self.backmap:
                self.backmap[mapping.channel.id] = []
            self.backmap[mapping.channel.id].append(mapping.channel_id)

        logger.info(f"Updated channel mapping info for {len(cmaps)} channels")

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.channel.id in self.mapping:
            channel = self.mapping[message.channel.id]
            self.bot.dispatch("channel_message", channel, self.backmap[channel.id], message)

    @Cog.listener()
    async def on_message_delete(self, message: Message) -> None:
        return

        # Return for now, since people are using this maliciously.

        if message.channel.id in self.mapping:
            ac = self.bot.get_cog("Admin")  # type: ignore

            ac: Admin

            await ac.delete_all(message)


def setup(bot: Bot) -> None:
    bot.add_cog(Listener(bot))
