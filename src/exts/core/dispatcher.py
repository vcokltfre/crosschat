from asyncio import create_task

from disnake import AllowedMentions, Embed, Member
from disnake import Message as DiscordMessage
from disnake import TextChannel
from disnake import User as DiscordUser
from disnake import Webhook
from disnake.ext.commands import Cog
from ormar import NoMatch

from src import Bot
from src.impl.database import Channel, Message, User


class Dispatcher(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.webhook_cache: dict[int, list[Webhook]] = {}
        self.user_cache: dict[int, User] = {}

    @Cog.listener()
    async def on_user_permissions_changed(self, user: User) -> None:
        self.user_cache[user.id] = user

    async def get_user(self, user: DiscordUser | Member) -> User:
        db_user = self.user_cache.get(user.id)

        if db_user is None:
            try:
                db_user = await User.objects.first(id=user.id)
            except NoMatch:
                db_user = await User(id=user.id, name=str(user)).save()

            self.user_cache[user.id] = db_user

        return db_user

    async def post_message(self, message: DiscordMessage, user: User, channel_id: int, cc_channel: Channel) -> None:
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            return

        if message.channel.id == channel.id:
            return

        assert isinstance(channel, TextChannel)

        hooks = self.webhook_cache.get(channel_id, [])

        if not hooks:
            hooks = await channel.webhooks() or [await channel.create_webhook(name="CrossChat")]

        self.webhook_cache[channel_id] = hooks

        kwargs = {}

        if message.reference:
            kwargs["embeds"] = [Embed(description=message.reference.resolved.content[:250])]  # type: ignore

            kwargs["embeds"][0].set_author(
                name=message.author,
                icon_url=message.reference.resolved.author.display_avatar.url,  # type: ignore
                url=message.reference.resolved.jump_url,  # type: ignore
            )

        msg = await hooks[0].send(
            message.content,
            username=message.author.name + user.badges,
            avatar_url=message.author.display_avatar.url,
            allowed_mentions=AllowedMentions(roles=False, everyone=False),
            wait=True,
            **kwargs,
        )

        assert msg.guild

        await Message(
            id=msg.id,
            channel=cc_channel.id,
            user=user.id,
            channel_id=msg.channel.id,
            guild_id=msg.guild.id,
            original_id=message.id,
        ).save()

    @Cog.listener()
    async def on_channel_message(self, channel: Channel, channels: list[int], message: DiscordMessage) -> None:
        if message.author.bot or not message.guild:
            return

        user = await self.get_user(message.author)

        if user.banned:
            return

        for c in channels:
            create_task(self.post_message(message, user, c, channel))

        await Message(
            id=message.id,
            channel=channel.id,
            user=user.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            original_id=message.id,
        ).save()


def setup(bot: Bot) -> None:
    bot.add_cog(Dispatcher(bot))
