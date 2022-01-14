from disnake import Interaction
from disnake.ext.commands import CheckFailure, Cog, MissingPermissions, NotOwner

from src import Bot


class ErrorHandler(Cog):
    @Cog.listener()
    async def on_slash_command_error(self, itr: Interaction, error: Exception) -> None:
        await self.handle_interaction_error(itr, error)

    @Cog.listener()
    async def on_message_command_error(self, itr: Interaction, error: Exception) -> None:
        await self.handle_interaction_error(itr, error)

    @Cog.listener()
    async def on_user_command_error(self, ctx: Interaction, error: Exception) -> None:
        await self.handle_interaction_error(ctx, error)

    async def handle_interaction_error(self, itr: Interaction, error: Exception) -> None:
        if isinstance(error, (MissingPermissions, NotOwner, CheckFailure)):
            await itr.send(f"You don't have the required permissions to do that.", ephemeral=True)
        else:
            await itr.send(f"An unknown error occurred while running the command :(", ephemeral=True)
            raise error


def setup(bot: Bot) -> None:
    bot.add_cog(ErrorHandler())
