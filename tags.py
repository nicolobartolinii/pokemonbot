from mongodb import *


class Tags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='createtag', aliases=['tagcreate', 'ct'])
    async def createtag(self, ctx: commands.Context, tag_name: str, emoji: discord.Emoji):
        pass

    @commands.command(name='tags')
    async def tags(self, ctx: commands):
        pass

    @createtag.error
    async def createtag_error(self, ctx: commands.Context, error):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Tags(bot))