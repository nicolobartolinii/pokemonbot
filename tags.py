from mongodb import *


class Tags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='createtag', aliases=['tagcreate', 'ct', 'tagadd', 'tc'])
    async def createtag(self, ctx: commands.Context, tag_name: str, emoji):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_tags = users.find_one({'_id': str(ctx.author.id)})['tags']
        try:
            if user_tags[tag_name] is not None:
                await ctx.send(f'Sorry {ctx.author.mention}, that tag could not be added because it already exists.')
                return
        except KeyError:
            users.update_one({'_id': str(ctx.author.id)}, {'$push': {f'tags.{tag_name}': ''}})
            users.update_one({'_id': str(ctx.author.id)}, {'$pull': {f'tags.{tag_name}': ''}})
            users.update_one({'_id': str(ctx.author.id)}, {'$set': {f'tagEmojis.{tag_name}': str(emoji)}})
            await ctx.send(f'{ctx.author.mention}, tag `{tag_name}` has been successfully created.')

    @commands.command(name='tags')
    async def tags(self, ctx: commands):
        pass

    @commands.command(name='tag', aliases=['t'])
    async def tag(self, ctx: commands.Context, tag_name: str, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user = users.find_one({'_id': str(ctx.author.id)})
        user_tags = user['tags']
        user_inventory = user['inventory']
        if card_code is None:
            card_code = user_inventory[-1]
        card_code = card_code.upper()
        if card_code not in user_inventory:
            await ctx.send(f'{ctx.author.mention}, you are not the owner of that card.')
            return
        try:
            user_tags[tag_name]
        except KeyError:
            await ctx.send(f'Sorry {ctx.author.mention}, that tag does not exist. You can create a new tag using the `createtag` command.')
            return
        for tag in user_tags.keys():
            tagged_cards = user_tags[tag]
            if card_code in tagged_cards:
                users.update_one(
                    {'_id': str(ctx.author.id)},
                    {'$pull': {f'tags.{tag}': str(card_code)}}
                )
        users.update_one(
            {'_id': str(ctx.author.id)},
            {'$push': {f'tags.{tag_name}': str(card_code)}}
        )
        card_id = grabbed_cards.find_one({'_id': str(card_code)})['cardId']
        card_name = cards.find_one({'_id': str(card_id)})['name']
        await ctx.send(f'{ctx.author.mention}, the **{card_name}** card has been tagged successfully with the `{tag_name}` tag.')

    @createtag.error
    async def createtag_error(self, ctx: commands.Context, error):
        await ctx.send('Something went wrong. Please use the `help` command to check the usage of commands.')


def setup(bot: commands.Bot):
    bot.add_cog(Tags(bot))
