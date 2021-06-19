import logging.config
import traceback
from logging import getLogger

import discord
from discord.ext import commands
from discord_slash import SlashCommand

from setting import TOKEN

logging.config.fileConfig('logging.conf')
logger = getLogger(__name__)

INITIAL_EXTENSIONS = [
    'cogs.clan_battle',
]


class MyBot(commands.Bot):

    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix, intents=intents)
        slash = SlashCommand(self, sync_commands=True)

        for cog in INITIAL_EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                traceback.print_exc()

    async def on_ready(self):
        logger.info("Login was successful.")
        logger.info(f"bot name: {self.user.name}")
        logger.info(f"bot id: {self.user.id}")


# MyBotのインスタンス化及び起動処理。
if __name__ == '__main__':
    intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
    bot = MyBot('.', intents)
    bot.run(TOKEN)  # Botのトークン
