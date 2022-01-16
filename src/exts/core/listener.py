from disnake import Message
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from ormar import NoMatch

from src import Bot
from src.impl.core import ChannelManager
from src.impl.database import User


class Listener(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.users: dict[int, User] = {}

    async def resolve_user(self, user_id: int, user_name: str) -> User:
        user = self.users.get(user_id)

        if user is None:
            try:
                user = await User.objects.first(id=user_id)
            except NoMatch:
                user = await User(id=user_id, name=str(user_name)).save()

            self.users[user.id] = user

        return user

    @loop(minutes=1)
    async def flush_cache(self) -> None:
        self.bot.ccache = {}

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        channel = self.bot.resolve_channel(message.channel.id)

        if channel is None or message.author.bot:
            return

        user = await self.resolve_user(message.author.id, message.author.name)

        if user.banned:
            return

        await channel.send(message.author.name, message.author.display_avatar.url, message.content, message, user)

    @Cog.listener()
    async def on_message_edit(self, _: Message, after: Message) -> None:
        channel = self.bot.resolve_channel(after.channel.id)

        if channel is None or after.author.bot:
            return

        user = await self.resolve_user(after.author.id, after.author.name)

        if user.banned:
            return

        await channel.edit(after.id, after.content)


def setup(bot: Bot) -> None:
    bot.add_cog(Listener(bot))
