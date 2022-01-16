from disnake import CommandInteraction, Embed
from disnake.ext.commands import Cog, Param, slash_command
from ormar import NoMatch

from src import Bot
from src.impl.database import Channel, ChannelMap, Message
from src.impl.utils import is_administrator


class Core(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(
        name="status",
        description="Get the status of the bot",
    )
    @is_administrator()
    async def status(self, itr: CommandInteraction) -> None:
        await itr.response.defer()

        channels = await Channel.objects.count()
        dchannels = await ChannelMap.objects.count()
        messages = await Message.objects.count()
        umessages = await Message.objects.filter(Message.id == Message.original_id).count()

        embed = Embed(
            title="CrossChat Status",
            colour=0x87CEEB,
            description=(
                f"Connected as {self.bot.user}\n"
                f"Latency: {self.bot.latency * 1000:.2f}ms\n"
                f"Guilds: {len(self.bot.guilds)}\n"
            ),
        )

        embed.add_field(
            name="Channels",
            value=f"Virtual: {channels}\nDiscord: {dchannels}",
        )

        embed.add_field(
            name="Messages",
            value=f"Total: {messages}\nUnique: {umessages}",
        )

        await itr.send(embed=embed)

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
