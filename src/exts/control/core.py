from disnake import CommandInteraction, TextChannel
from disnake.ext.commands import Cog, Param, slash_command
from ormar import NoMatch

from src import Bot
from src.impl.database import Channel, ChannelMap
from src.impl.utils import is_administrator


class Core(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(
        name="status",
        description="Get the status of the bot",
    )
    async def status(self, itr: CommandInteraction) -> None:
        pass

    @slash_command(
        name="setup",
        description="Setup a channel for CrossChat",
    )
    @is_administrator()
    async def setup(
        self,
        itr: CommandInteraction,
        channel: str = Param(desc="The CrossChat channel to connect to"),
    ) -> None:
        try:
            db_channel = await Channel.objects.first(name=channel)
        except NoMatch:
            await itr.send(f"Channel {channel} does not exist.", ephemeral=True)
            return

        cmap = await ChannelMap(channel=db_channel, channel_id=itr.channel.id).save()

        self.bot.dispatch("channel_mapped", cmap)

        await itr.send(f"Mapped channel {itr.channel.id} to CC:{channel}")

    @slash_command(
        name="unlink",
        description="Unlink a channel from CrossChat",
    )
    @is_administrator()
    async def unlink(
        self,
        itr: CommandInteraction,
        channel: str = Param(desc="The CrossChat channel to unlink"),
    ) -> None:
        try:
            cmap = await ChannelMap.objects.first(channel_id=itr.channel.id)
        except NoMatch:
            await itr.send(f"This channel is not linked.", ephemeral=True)
            return

        await cmap.delete()

        await itr.send(f"Unlinked channel {itr.channel.id} from CC:{channel}")

        self.bot.dispatch("channel_unmapped", cmap)


def setup(bot: Bot) -> None:
    bot.add_cog(Core(bot))
