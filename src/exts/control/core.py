from disnake import CommandInteraction, Embed, Thread
from disnake.ext.commands import Cog, Param, slash_command

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
            value=f"Total: {messages}",
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
        vchannel = self.bot.vchannels.get(channel, None)

        if vchannel is None:
            await itr.send(f"Channel {channel} does not exist.")
            return

        if isinstance(itr.channel, Thread):
            await vchannel.join(itr.channel.parent_id, itr.channel.id)
        else:
            await vchannel.join(itr.channel.id)

        await itr.send(f"Mapped channel {itr.channel.id} to CC:{channel}")

    @slash_command(
        name="unlink",
        description="Unlink a channel from CrossChat",
    )
    @is_administrator()
    async def unlink(
        self,
        itr: CommandInteraction,
    ) -> None:
        vchannel = self.bot.resolve_channel(itr.channel.id)

        if vchannel is None:
            await itr.send(f"Channel {itr.channel.id} is not linked.")
            return

        await vchannel.leave(itr.channel.id)

        await itr.send(f"Unlinked channel {itr.channel.id} from CC:{vchannel.channel.name}")


def setup(bot: Bot) -> None:
    bot.add_cog(Core(bot))
