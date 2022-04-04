from mongodb import *


class Tags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='createtag', aliases=['tagcreate', 'ct', 'tagadd', 'tc'])
    async def createtag(self, ctx: commands.Context, tag_name: str, emoji: discord.Emoji):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_tags = users.find_one({'_id': str(ctx.author.id)})['tags']
        try:
            if user_tags[tag_name] is not None:
                await ctx.send(f'Sorry {ctx.author.mention}, that tag could not be added because it already exists.')
                return
        except KeyError:
            pass
        users.update_one({'_id': str(ctx.author.id)}, {'$push': {f'tags.{tag_name}': []}})
        users.update_one({'_id': str(ctx.author.id)}, {'$push': {f'tagEmojis.{tag_name}': str(emoji)}})
        await ctx.send(f'{ctx.author.mention}, tag `{tag_name}` has been successfully created.')

    @commands.command(name='tags')
    async def tags(self, ctx: commands):
        pass

    @createtag.error
    async def createtag_error(self, ctx: commands.Context, error):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Tags(bot))