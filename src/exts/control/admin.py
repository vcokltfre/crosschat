from disnake import CommandInteraction, Embed
from disnake import User as DiscordUser
from disnake import Webhook
from disnake.ext.commands import Cog, Param, is_owner, slash_command
from ormar import NoMatch

from src import Bot
from src.impl.core import ChannelManager
from src.impl.database import Channel, User


class Admin(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self._webhook: Webhook | None = None

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
        public: bool = Param(False, desc="Whether the channel should be public"),
    ) -> None:
        channel = await Channel(name=name, flags=int(public)).save()

        await itr.send(f"Created channel {channel.name} ({channel.flags})", ephemeral=True)

        self.bot.vchannels[name] = ChannelManager(self.bot, channel)

        await self.bot.vchannels[name].setup()

    @channels_group.sub_command(
        name="delete",
        description="Delete a CrossChat channel",
    )
    @is_owner()
    async def delete_channel(
        self,
        itr: CommandInteraction,
        name: str = Param(desc="The name of the channel to delete"),
    ) -> None:
        try:
            channel = await Channel.get(name=name)
        except NoMatch:
            await itr.send(f"Channel {name} does not exist.", ephemeral=True)
            return

        await channel.delete()

        self.bot.vchannels.pop(name, None)

    @slash_command(
        name="permissions",
        description="Modify permissions for a user",
    )
    @is_owner()
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

    @slash_command(
        name="announce",
        description="Announce a message to all channels",
    )
    @is_owner()
    async def announce(
        self,
        itr: CommandInteraction,
        channel: str = Param(desc="The CrossChat channel to announce to"),
        message: str = Param(desc="The message to announce"),
    ) -> None:
        await itr.response.defer(ephemeral=True)

        vchannel = self.bot.vchannels.get(channel, None)

        if not vchannel:
            await itr.send(f"Channel {channel} does not exist.", ephemeral=True)
            return

        embed = Embed(
            title="Announcement",
            description=message,
            color=0x87CEEB,
        )

        embed.set_author(name="System", icon_url="https://cdn.discordapp.com/emojis/931546588235595796.png")

        await vchannel.send("CrossChat", self.bot.user.display_avatar.url, embeds=[embed], content=None)  # type: ignore

        await itr.send(f"Announced to {channel} ({len(vchannel.channels)} subchannels)", ephemeral=True)


def setup(bot: Bot) -> None:
    bot.add_cog(Admin(bot))
