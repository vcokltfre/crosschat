from cachingutils import cached
from disnake import Embed, Message
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from ormar import NoMatch

from src import Bot
from src.impl.database import User


class Listener(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @staticmethod
    @cached()
    def shorten(message: str) -> str:
        if len(message) <= 2000:
            return message
        return message[:1997] + "..."

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
            resolved: Message = message.reference.resolved  # type: ignore

            embed = Embed(
                colour=0x87CEEB,
                description=f"{resolved.content[:500]}",
                timestamp=resolved.created_at,
            )

            embed.set_author(
                name=resolved.author.name,
                icon_url=resolved.author.display_avatar.url,
            )

            kwargs["embeds"].append(embed)

        if message.attachments and (message.attachments[0].content_type or "").startswith("image/"):
            embed = Embed()

            embed.set_image(url=message.attachments[0].url)

            kwargs["embeds"].append(embed)

        if not kwargs["embeds"]:
            kwargs.pop("embeds")

        await channel.send(
            message.author.name,
            message.author.display_avatar.url,
            self.shorten(message.content),
            message,
            user,
            **kwargs,
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
