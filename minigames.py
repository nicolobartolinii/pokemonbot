import asyncio

from mongodb import *
import time


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='minigame', aliases=['mg'])
    async def minigame(self, ctx: commands.Context):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Profile(bot))
