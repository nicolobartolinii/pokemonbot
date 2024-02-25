import asyncio

from mongodb import *


class Wishlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='wishlist', aliases=['w', 'wl'])
    async def wishlist(self, ctx: commands.Context, *, member: discord.Member = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose wishlist you are looking for is not registered. He should register an account using the `start` command.')
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
                card = cards.find_one({'_id': str(wishlist[i])})
                card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                embed.description += card_str
            embed.set_footer(text=f'Showing wishlisted cards 1-{len(wishlist)}')
            await ctx.send(embed=embed)
        elif len(wishlist) >= 10:
            for i in range(10):
                card = cards.find_one({'_id': str(wishlist[i])})
                card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                embed.description += card_str
            embed.set_footer(text=f'Showing cards 1-10 of {len(wishlist)}')
            message = await ctx.send(embed=embed)

            embeds = [embed]
            pages = (len(wishlist) // 10) + 1
            for p in range(1, pages):
                next_page = discord.Embed(title=f"Wishlist", description=f'Owner: {member.mention}\n[WIP slots extra]\n\n', colour=0xffcb05)
                next_page.set_thumbnail(url=member.avatar_url)
                for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(wishlist) else len(wishlist)):
                    card = cards.find_one({'_id': str(wishlist[i])})
                    card_str = f'{str(card["set"])} · **{str(card["name"])}**\n'
                    next_page.description += card_str
                next_page.set_footer(text=f'Showing wishlisted cards {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(wishlist) else len(wishlist)} of {len(wishlist)}')
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
    async def wishadd(self, ctx: commands.Context, *, card_name: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if card_name is None:
            await ctx.send(f'{ctx.author.mention}, please specify a card name.')
            return
        else:
            cards_filtered = list(cards.find({'name': {'$regex': f".*{card_name}.*", '$options': 'i'}}))
            user = users.find_one({'_id': str(ctx.author.id)})
            wishlist = user['wishlist']
            if len(cards_filtered) == 0:
                await ctx.send(f'Sorry {ctx.author.mention}, that card could not be found. It may not exist, or you may have misspelled its name.')
                return
            elif len(cards_filtered) == 1:
                card_id = cards_filtered[0]['_id']
                if card_id in wishlist:
                    await ctx.send(f'{ctx.author.mention}, `{cards_filtered[0]["name"]} · {cards_filtered[0]["set"]}` is already in your wishlist.')
                    return
                users.update_one({'_id': str(ctx.author.id)}, {'$push': {'wishlist': str(card_id)}})
                cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': 1}})
                await ctx.send(f'{ctx.author.mention}, `{cards_filtered[0]["name"]} · {cards_filtered[0]["set"]}` has been successfully added to your wishlist.')
            else:
                embed = discord.Embed(title='Card Results', description=f'{ctx.author.mention}, please type the number that corresponds to the card you are looking for.', colour=0xffcb05)
                field_text = ''
                if len(cards_filtered) < 10:
                    for i in range(len(cards_filtered)):
                        card_wishlists = cards_filtered[i]['wishlists']
                        card_name = cards_filtered[i]['name']
                        card_set = cards_filtered[i]['set']
                        card_rarity = cards_filtered[i]['rarity']
                        field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                    embed.add_field(
                        name=f'Showing wishlistable cards 1-{len(cards_filtered)}',
                        value=field_text)
                    await ctx.send(embed=embed)
                else:
                    for i in range(10):
                        card_wishlists = cards_filtered[i]['wishlists']
                        card_name = cards_filtered[i]['name']
                        card_set = cards_filtered[i]['set']
                        card_rarity = cards_filtered[i]['rarity']
                        field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                    embed.add_field(
                        name=f'Showing wishlistable 1-10 of {len(cards_filtered)}',
                        value=field_text)
                    message = await ctx.send(embed=embed)

                    embeds = [embed]
                    pages = (len(cards_filtered) // 10) + 1
                    for p in range(1, pages):
                        next_page = discord.Embed(title='Card Results', description=f'{ctx.author.mention}, please type the number that corresponds to the card you are looking for.', colour=0xffcb05)
                        field_text = ''
                        for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)):
                            card_wishlists = cards_filtered[i]['wishlists']
                            card_name = cards_filtered[i]['name']
                            card_set = cards_filtered[i]['set']
                            card_rarity = cards_filtered[i]['rarity']
                            field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                        next_page.add_field(
                            name=f'Showing wishlistable {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)} of {len(cards_filtered)}',
                            value=field_text)
                        embeds.append(next_page)
                    cur_page = 0

                    await message.add_reaction('⬅')
                    await message.add_reaction('➡')

                    def check(r: discord.Reaction, u):
                        return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

                    while True:
                        tasks = [
                                asyncio.create_task(self.bot.wait_for('reaction_add', timeout=30, check=check), name='r'),
                                asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == ctx.author and int(m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel, timeout=30), name='m')
                            ]

                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                        finished: asyncio.Task = list(done)[0]

                        for task in pending:
                            try:
                                task.cancel()
                            except asyncio.CancelledError:
                                pass

                        action = finished.get_name()
                        try:
                            result = finished.result()
                        except asyncio.TimeoutError:
                            return

                        if action == 'r':
                            reaction, user = result
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
                        elif action == 'm':
                            msg = result
                            card_id = cards_filtered[int(msg.content) - 1]['_id']
                            if card_id in wishlist:
                                await ctx.send(
                                    f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` is already in your wishlist.')
                                return
                            users.update_one({'_id': str(ctx.author.id)}, {'$push': {'wishlist': str(card_id)}})
                            cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': 1}})
                            await ctx.send(
                                f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` has been successfully added to your wishlist.')
                            return
                try:
                    msg = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == ctx.author and int(m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel,
                        timeout=30
                    )
                except asyncio.TimeoutError:
                    return

                card_id = cards_filtered[int(msg.content) - 1]['_id']
                if card_id in wishlist:
                    await ctx.send(
                        f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` is already in your wishlist.')
                    return
                users.update_one({'_id': str(ctx.author.id)}, {'$push': {'wishlist': str(card_id)}})
                cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': 1}})
                await ctx.send(
                    f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` has been successfully added to your wishlist.')

    @commands.command(name='wishremove', aliases=['wr', 'wrem'])
    async def wishremove(self, ctx: commands.Context, *, card_name: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if card_name is None:
            await ctx.send(f'{ctx.author.mention}, please specify a card name.')
            return
        else:
            user = users.find_one({'_id': str(ctx.author.id)})
            wishlist = user['wishlist']
            cards_filtered = list(cards.find({
                'name': {'$regex': f".*{card_name}.*", '$options': 'i'},
                '_id': {'$in': wishlist}
            }))
            if len(cards_filtered) == 0:
                await ctx.send(f'Sorry {ctx.author.mention}, that card could not be found. It may not exist, or you may have misspelled its name.')
                return
            elif len(cards_filtered) == 1:
                card_id = cards_filtered[0]['_id']
                if card_id not in wishlist:  # Potrebbe non servire questo if
                    await ctx.send(f'{ctx.author.mention}, `{cards_filtered[0]["name"]} · {cards_filtered[0]["set"]}` is not in your wishlist.')
                    return
                users.update_one({'_id': str(ctx.author.id)}, {'$pull': {'wishlist': str(card_id)}})
                cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': -1}})
                await ctx.send(f'{ctx.author.mention}, `{cards_filtered[0]["name"]} · {cards_filtered[0]["set"]}` has been successfully removed from your wishlist.')
            else:
                embed = discord.Embed(title='Card Results', description=f'{ctx.author.mention}, please type the number that corresponds to the card you are looking for.', colour=0xffcb05)
                field_text = ''
                if len(cards_filtered) < 10:
                    for i in range(len(cards_filtered)):
                        card_wishlists = cards_filtered[i]['wishlists']
                        card_name = cards_filtered[i]['name']
                        card_set = cards_filtered[i]['set']
                        card_rarity = cards_filtered[i]['rarity']
                        field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                    embed.add_field(
                        name=f'Showing cards 1-{len(cards_filtered)}',
                        value=field_text)
                    await ctx.send(embed=embed)
                else:
                    for i in range(10):
                        card_wishlists = cards_filtered[i]['wishlists']
                        card_name = cards_filtered[i]['name']
                        card_set = cards_filtered[i]['set']
                        card_rarity = cards_filtered[i]['rarity']
                        field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                    embed.add_field(
                        name=f'Showing wishlistable 1-10 of {len(cards_filtered)}',
                        value=field_text)
                    message = await ctx.send(embed=embed)

                    embeds = [embed]
                    pages = (len(cards_filtered) // 10) + 1
                    for p in range(1, pages):
                        next_page = discord.Embed(title='Card Results', description=f'{ctx.author.mention}, please type the number that corresponds to the card you are looking for.', colour=0xffcb05)
                        field_text = ''
                        for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)):
                            card_wishlists = cards_filtered[i]['wishlists']
                            card_name = cards_filtered[i]['name']
                            card_set = cards_filtered[i]['set']
                            card_rarity = cards_filtered[i]['rarity']
                            field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                        next_page.add_field(
                            name=f'Showing {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)} of {len(cards_filtered)}',
                            value=field_text)
                        embeds.append(next_page)
                    cur_page = 0

                    await message.add_reaction('⬅')
                    await message.add_reaction('➡')

                    def check(r: discord.Reaction, u):
                        return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

                    while True:
                        tasks = [
                                asyncio.create_task(self.bot.wait_for('reaction_add', timeout=30, check=check), name='r'),
                                asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == ctx.author and int(m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel, timeout=30), name='m')
                            ]

                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                        finished: asyncio.Task = list(done)[0]

                        for task in pending:
                            try:
                                task.cancel()
                            except asyncio.CancelledError:
                                pass

                        action = finished.get_name()
                        try:
                            result = finished.result()
                        except asyncio.TimeoutError:
                            return

                        if action == 'r':
                            reaction, user = result
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
                        elif action == 'm':
                            msg = result
                            card_id = cards_filtered[int(msg.content) - 1]['_id']
                            if card_id not in wishlist:  # Potrebbe non servire questo if
                                await ctx.send(
                                    f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` is not in your wishlist.')
                                return
                            users.update_one({'_id': str(ctx.author.id)}, {'$pull': {'wishlist': str(card_id)}})
                            cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': -1}})
                            await ctx.send(
                                f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` has been successfully removed from your wishlist.')
                            return
                try:
                    msg = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == ctx.author and int(m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel,
                        timeout=30
                    )
                except asyncio.TimeoutError:
                    return

                card_id = cards_filtered[int(msg.content) - 1]['_id']
                if card_id not in wishlist:  # Potrebbe non servire questo if
                    await ctx.send(
                        f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` is not in your wishlist.')
                    return
                users.update_one({'_id': str(ctx.author.id)}, {'$pull': {'wishlist': str(card_id)}})
                cards.update_one({'_id': str(card_id)}, {'$inc': {'wishlists': -1}})
                await ctx.send(
                    f'{ctx.author.mention}, `{cards_filtered[int(msg.content) - 1]["name"]} · {cards_filtered[int(msg.content) - 1]["set"]}` has been successfully removed from your wishlist.')

    @commands.command(name='wishwatch', aliases=['ww', 'wishw', 'wwatch'])
    async def wishwatch(self, ctx: commands.Context):
        guilds.update_one(
            {'_id': str(ctx.guild.id)},
            {'$push': {'wishWatching': str(ctx.author.id)}}
        )
        wish_watching = users.find_one({'_id': str(ctx.author.id)})['wishWatching']
        if wish_watching != '':
            guilds.update_one(
                {'_id': str(wish_watching)},
                {'$pull': {'wishWatching': str(ctx.author.id)}}
            )
        users.update_one(
            {'_id': str(ctx.author.id)},
            {'$set': {'wishWatching': str(ctx.guild.id)}}
        )
        await ctx.send(f'{ctx.author.mention}, your wishlist watch channel has been set to this channel.')


def setup(bot: commands.Bot):
    bot.add_cog(Wishlist(bot))
