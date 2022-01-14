from os import environ

from disnake import Intents

from . import Bot


def main() -> None:
    intents = Intents.none()

    intents.guilds = True
    intents.members = True
    intents.guild_messages = True

    bot = Bot(intents=intents, text_guilds=[683009037830324235])

    for ext in [
        "src.exts.errors",
        "src.exts.control.admin",
        "src.exts.control.core",
        "src.exts.core.dispatcher",
        "src.exts.core.listener",
    ]:
        bot.load_extension(ext)

    bot.run(environ["TOKEN"])


main()
