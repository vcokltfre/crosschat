from disnake import CommandInteraction
from disnake.ext.commands import check
from ormar import NoMatch

from src.impl.database import User


def is_administrator():
    async def predicate(ctx: CommandInteraction) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True

        try:
            user = await User.objects.first(id=ctx.author.id)
        except NoMatch:
            return False

        return user.user_flags.ADMIN

    return check(predicate)  # type: ignore


def is_moderator():
    async def predicate(ctx: CommandInteraction) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True

        try:
            user = await User.objects.first(id=ctx.author.id)
        except NoMatch:
            return False

        return user.user_flags.ADMIN or user.user_flags.MODERATOR

    return check(predicate)  # type: ignore
