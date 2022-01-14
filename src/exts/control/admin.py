from disnake import CommandInteraction
from disnake import Message as DiscordMessage
from disnake import User as DiscordUser
from disnake.ext.commands import Cog, Param, is_owner, message_command, slash_command
from disnake.http import Route
from loguru import logger
from ormar import NoMatch

from src import Bot
from src.impl.database import Channel, Message, User
from src.impl.utils import is_moderator


class Admin(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(
        name="channels",
        description="Channel commands",
    )
    async def channels_group(self, itr: CommandInteraction) -> None:
        pass

    @channels_group.sub_command(
        name="create",
        description="Create a new CrossChat channel",
    )
    @is_owner()
    async def create_channel(
        self,
        itr: CommandInteraction,
        name: str = Param(desc="The name of the channel to create"),
        public: bool = Param(False, desc="Whether the channel should be public [False]"),
    ) -> None:
        channel = await Channel(id=self.bot.sf.generate(), name=name, flags=int(public)).save()

        await itr.send(f"Created channel {channel.name} ({channel.id}, {channel.flags})", ephemeral=True)

    @channels_group.sub_command(
        name="delete",
        description="Delete a CrossChat channel",
    )
    @is_owner()
    async def delete_channel(
        self,
        itr: CommandInteraction,
        id: int = Param(desc="The ID of the channel to delete"),
    ) -> None:
        try:
            channel = await Channel.get(id=id)
        except NoMatch:
            await itr.send(f"Channel {id} does not exist.", ephemeral=True)
            return

        await channel.delete()

        await itr.send(f"Deleted channel {channel.name} ({channel.id}, {channel.flags})", ephemeral=True)

    @slash_command(
        name="permissions",
        description="Modify permissions for a user",
    )
    async def permissions(
        self,
        itr: CommandInteraction,
        user: DiscordUser = Param(desc="The user to modify permissions for"),
        permissions: int = Param(desc="The new permissions for the user"),
    ) -> None:
        try:
            db_user = await User.objects.first(id=user.id)
            await db_user.update(flags=permissions)
        except NoMatch:
            db_user = await User(id=user.id, flags=permissions, name=str(user)).save()

        await itr.send(f"User {user.id} now has permissions {bin(permissions)[2:]}", ephemeral=True)

        self.bot.dispatch("user_permissions_changed", db_user)

    @message_command(name="Delete CC Message")
    @is_moderator()
    async def delete_message(self, itr: CommandInteraction, message: DiscordMessage) -> None:
        await itr.response.defer(ephemeral=True)

        try:
            await self.delete_all(message)
        except NoMatch:
            await itr.send(f"Message {message.id} is not a CrossChat message.", ephemeral=True)

        await itr.send("Message deleted.", ephemeral=True)

    async def delete_all(self, message: DiscordMessage) -> None:
        db_msg = await Message.objects.first(id=message.id)

        messages = await Message.objects.filter(original_id=db_msg.original_id).all()

        for msg in messages:
            try:
                channel = self.bot.get_channel(msg.channel_id)

                if not channel:
                    continue

                route = Route(
                    "DELETE", "/channels/{channel_id}/messages/{message_id}", channel_id=channel.id, message_id=msg.id
                )

                await msg.update(flags=msg.flags | 1)
                await self.bot.http.request(route)
            except Exception as e:
                logger.error(str(e))


def setup(bot: Bot) -> None:
    bot.add_cog(Admin(bot))
