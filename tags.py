import asyncio

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
            if str(emoji) == '◾':
                await ctx.send(
                    f'Sorry {ctx.author.mention}, that emoji cannot be used because it is used for technical purposes.')
                return
            users.update_one({'_id': str(ctx.author.id)}, {'$push': {f'tags.{tag_name}': ''}})
            users.update_one({'_id': str(ctx.author.id)}, {'$pull': {f'tags.{tag_name}': ''}})
            users.update_one({'_id': str(ctx.author.id)}, {'$set': {f'tagEmojis.{tag_name}': str(emoji)}})
            await ctx.send(f'{ctx.author.mention}, tag `{tag_name}` has been successfully created.')

    @commands.command(name='deletetag', aliases=['tagdelete', 'dt', 'td'])
    async def deletetag(self, ctx: commands.Context, tag_name: str):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_tags = users.find_one({'_id': str(ctx.author.id)})['tags']
        try:
            user_tags[tag_name]
        except KeyError:
            await ctx.send(f'Sorry {ctx.author.mention}, that tag could not be deleted because it does not exist.')
            return
        users.update_one({'_id': str(ctx.author.id)}, {'$unset': {f'tags.{tag_name}': 1}})
        users.update_one({'_id': str(ctx.author.id)}, {'$unset': {f'tagEmojis.{tag_name}': 1}})
        await ctx.send(f'{ctx.author.mention}, tag `{tag_name}` has been successfully deleted.')

    @commands.command(name='tags')
    async def tags(self, ctx: commands.Context, member: discord.Member = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose tags you are looking for is not registered. He should register an account using the `start` command.')
            return
        if member is None:
            member = ctx.author
        user = users.find_one({'_id': str(member.id)})
        tags = user['tags']
        embed = discord.Embed(title='Tags', description=f"{member.mention}'s tags.\n\n",
                              colour=0xffcb05)
        if len(tags) == 0:
            embed.description += 'Tags list is empty.'
            await ctx.send(embed=embed)
            return
        tags_list_str = []
        for tag_name in tags:
            tag_emoji = user['tagEmojis'][tag_name]
            tag_cards = len(tags[tag_name])
            tag_str = f'{tag_emoji}`{tag_name}` · **{tag_cards}** {"cards" if tag_cards != 1 else "card"}\n'
            tags_list_str.append(tag_str)
        if len(tags) < 10:
            for i in range(len(tags)):
                embed.description += tags_list_str[i]
            embed.set_footer(text=f'Showing tags 1-{len(tags)}')
            await ctx.send(embed=embed)
        elif len(tags) >= 10:
            for i in range(10):
                embed.description += tags_list_str[i]
            embed.set_footer(text=f'Showing tags 1-10 of {len(tags)}')
            message = await ctx.send(embed=embed)

            embeds = [embed]
            pages = (len(tags) // 10) + 1
            for p in range(1, pages):
                next_page = discord.Embed(title='Tags',
                                          description=f"{member.mention}'s tags.\n\n", colour=0xffcb05)
                for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(tags) else len(tags)):
                    next_page.description += tags_list_str[i]
                next_page.set_footer(
                    text=f'Showing tags {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(tags) else len(tags)} of {len(tags)}')
                embeds.append(next_page)
            cur_page = 0

            await message.add_reaction('⬅')
            await message.add_reaction('➡')

            def check(r: discord.Reaction, u):
                return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=45, check=check)

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

    @deletetag.error
    async def deletetag_error(self, ctx: commands.Context, error):
        await ctx.send('Something went wrong. Please use the `help` command to check the usage of commands.')

    @tag.error
    async def tag_error(self, ctx: commands.Context, error):
        await ctx.send('Something went wrong. Please use the `help` command to check the usage of commands.')


def setup(bot: commands.Bot):
    bot.add_cog(Tags(bot))
