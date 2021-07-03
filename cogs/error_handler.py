  
from logging import getLogger

from discord.ext import commands

logger = getLogger(__name__)

class ErrorHandler(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(
            error, commands.CommandNotFound
        ):
            return
        else:
            logger.error(error)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
