import asyncio

from mongodb import *


class Wishlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='wishlist', aliases=['w', 'wl'])
    async def wishlist(self, ctx: commands.Context, *, member: discord.Member = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `p$start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose wishlist you are looking for is not registered. He should register an account using the `p$start` command.')
            return
        if member is None:
            member = ctx.author
        embed = discord.Embed(title=f"Wishlist", description=f'Owner: {member.mention}\n[WIP slots extra]\n\n', colour=0xffcb05)
        embed.set_thumbnail(url=member.avatar_url)
        user = users.find_one({'_id': str(member.id)})
        wishlist = user['wishlist']
        if len(wishlist) == 0:
            embed.description += 'Wishlist is empty.'
            await ctx.send(embed=embed)
            return
        elif len(wishlist) < 10:
            for i in range(len(wishlist)):
                card = cards.fine_one({'_id': str(wishlist[i])})
                card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                embed.description += card_str
            embed.set_footer(text=f'Showing wishlisted cards 1-{len(wishlist)}')
            await ctx.send(embed=embed)
        elif len(wishlist) >= 10:
            for i in range(10):
                card = cards.fine_one({'_id': str(wishlist[i])})
                card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                embed.description += card_str
            embed.set_footer(text=f'Showing cards 1-10 of {len(wishlist)}')
            message = await ctx.send(embed=embed)

            embeds = [embed]
            pages = (len(wishlist) // 10) + 1
            for p in range(1, pages):
                next_page = discord.Embed(title=f"Wishlist", description=f'Owner: {member.mention}\n[WIP slots extra]\n\n', colour=0xffcb05)
                for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(wishlist) else len(wishlist)):
                    card = cards.fine_one({'_id': str(wishlist[i])})
                    card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                    embed.description += card_str
                embed.set_footer(text=f'Showing wishlisted cards {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(wishlist) else len(wishlist)} of {len(wishlist)}')
                embeds.append(next_page)
            cur_page = 0

            await message.add_reaction('⬅')
            await message.add_reaction('➡')

            def check(r: discord.Reaction, u):
                return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=15, check=check)

                    if str(reaction.emoji) == '➡' and cur_page != pages - 1:
                        cur_page += 1
                        await message.edit(embed=embeds[cur_page])
                        await message.remove_reaction(reaction, user)
                    elif str(reaction.emoji) == '⬅' and cur_page > 0:
                        cur_page -= 1
                        await message.edit(embed=embeds[cur_page])
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break

    @commands.command(name='wishadd', aliases=['wa', 'wadd'])
    async def wishadd(self, ctx: commands.Context, *, card_query: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `p$start` command.')
            return
        if card_query is None:
            await ctx.send(f'{ctx.author.mention}, please specify a card name.')
            return

    @commands.command(name='wishremove', aliases=['wr', 'wrem'])
    async def wishremove(self, ctx: commands.Context, *, card_query: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `p$start` command.')
            return
        if card_query is None:
            await ctx.send(f'{ctx.author.mention}, please specify a card name.')
            return


def setup(bot: commands.Bot):
    bot.add_cog(Wishlist(bot))
