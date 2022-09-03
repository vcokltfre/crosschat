from os import environ

from disnake import Intents

from . import Bot


def main() -> None:
    intents = Intents.none()

    intents.guilds = True
    intents.members = True
    intents.guild_messages = True
    intents.message_content = True

    kwargs = {}

    if guilds := environ.get("TEST_GUILDS"):
        kwargs["test_guilds"] = [int(guild) for guild in guilds.split(",")]

    bot = Bot(intents=intents, **kwargs)

    for ext in [
        "src.exts.errors",
        "src.exts.control.admin",
        "src.exts.control.core",
        "src.exts.core.listener",
    ]:
        bot.load_extension(ext)

    bot.run(environ["TOKEN"])


main()
