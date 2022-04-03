from mongodb import *


class Trades(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='give', aliases=['g'])
    async def give(self, ctx: commands.Context, member: discord.Member, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if ctx.guild.get_member(member.id) is None:
            await ctx.send(f'User not found.')
            return
        if not is_user_registered(member):
            await ctx.send('The member you want to give the card to is not registered. He should register an account using the `start` command.')
            return
        if ctx.author.id == member.id:
            await ctx.send(f'Sorry {ctx.author.mention}, you cannot give cards to yourself.')
            return
        user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
        if card_code is None:
            card_code = user_inventory[-1]
        card_code = card_code.upper()
        if card_code not in user_inventory:
            await ctx.send(f'{ctx.author.mention}, you do not have this card.')
            return

        giving = grabbed_cards.find_one({'_id': str(card_code)})
        card_id = giving['cardId']
        card_print = giving['print']
        generic_card = cards.find_one({'_id': str(card_id)})
        card_wishlists = generic_card['wishlists']
        card_set = generic_card['set']
        card_name = generic_card['name']
        card_image = f'./imagesHigh/{card_id.split("-")[0]}_{card_id.split("-")[1]}_hires.png'
        embed = discord.Embed(title='Card Transfer', description=f'{ctx.author.mention}`→`{member.mention}\n\n', colour=0xffcb05)
        embed.description += f'`{card_code}` · `#{card_print}` · `♡{str(card_wishlists)}` · {card_set} · **{card_name}**\n'
        file = discord.File(card_image, filename='image.png')
        embed.set_image(url=f'attachment://image.png')
        await ctx.send(file=file, embed=embed)



def setup(bot: commands.Bot):
    bot.add_cog(Trades(bot))