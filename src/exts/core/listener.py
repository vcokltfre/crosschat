from disnake import Embed, Message
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from ormar import NoMatch

from src import Bot
from src.impl.database import User


class Listener(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @loop(minutes=1)
    async def flush_cache(self) -> None:
        self.bot.ccache = {}

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        channel = self.bot.resolve_channel(message.channel.id)

        if channel is None or message.author.bot:
            return

        user = await self.bot.resolve_user(message.author.id, message.author.name)

        if user.banned:
            return

        kwargs = {"embeds": []}

        if message.reference:
            embed = Embed(
                colour=0x87CEEB,
                description=f"{message.reference.resolved.content[:500]}",  # type: ignore
                timestamp=message.reference.resolved.created_at,  # type: ignore
            )

            embed.set_author(
                name=message.reference.resolved.author.name,  # type: ignore
                icon_url=message.reference.resolved.author.display_avatar.url,  # type: ignore
            )

            kwargs["embeds"].append(embed)

        if not kwargs["embeds"]:
            kwargs.pop("embeds")

        await channel.send(
            message.author.name, message.author.display_avatar.url, message.content, message, user, **kwargs
        )

    @Cog.listener()
    async def on_message_edit(self, _: Message, after: Message) -> None:
        channel = self.bot.resolve_channel(after.channel.id)

        if channel is None or after.author.bot:
            return

        user = await self.bot.resolve_user(after.author.id, after.author.name)

        if user.banned:
            return

        await channel.edit(after.id, after.content)


def setup(bot: Bot) -> None:
    bot.add_cog(Listener(bot))
