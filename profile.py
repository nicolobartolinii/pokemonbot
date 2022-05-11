import asyncio

from mongodb import *
import time


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='profile', aliases=['p'])
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose collection you are looking for is not registered. He should register an account using the `start` command.')
            return
        if member is None:
            member = ctx.author
        user = users.find_one({'_id': str(member.id)})
        embed = discord.Embed(title='User details', description='', colour=0xffcb05)  # int(user['profileColor'], base=16))
        embed.set_author(name=member.name, icon_url=user['favouritePokemon'] if not None else member.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)  # TODO sprite pokemon preferito OR avatar
        embed.description = f'Level · **{user["level"]}**/20\n'
        embed.description += f'Experience · **{user["exp"]}** (**{round(((user["exp"] - EXP_AMOUNT[user["level"]])/(EXP_AMOUNT[user["level"] + 1] - EXP_AMOUNT[user["level"]]))*100, 1)}%** to level **{user["level"] + 1}**)\n\n'
        embed.description += f'Favourite Pokémon · WIP\n\n'  # TODO
        embed.description += f'Cards in collection · **{len(user["inventory"])}**\n'
        embed.description += f'Last card grabbed · `{user["inventory"][-1] if len(user["inventory"]) != 0 else "None"}`\n'
        embed.description += f'Cards grabbed · **{int(user["cardsGrabbed"])}**\n'
        embed.description += f'Cards spawned · **{int(user["cardsDropped"])}**\n'
        embed.description += f'Cards given · **{int(user["cardsGiven"])}**\n'
        embed.description += f'Cards received · **{int(user["cardsReceived"])}**\n'
        embed.description += f'Cards burned · **{int(user["cardsBurned"])}** (WIP)\n'
        embed.description += f'Minigames played · WIP\n'  # TODO
        embed.description += f'Minigames won · WIP\n'  # TODO
        playing_since = str(user['registeredAt'])
        date_registration = datetime.strptime(playing_since, '%m/%d/%Y, %H:%M:%S')
        date_registration_unix = time.mktime(date_registration.timetuple())
        embed.description += f'Playing since · <t:{str(int(date_registration_unix))}:F>'
        embed.add_field(name='Quick Inventory', value='WIP', inline=False)  # TODO
        await ctx.send(embed=embed)

    @commands.command(name='level', aliases=['lvl'])
    async def level(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user = users.find_one({'_id': str(ctx.author.id)})
        embed = discord.Embed(title='Level details', description='', colour=0xffcb05)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.description += f'Your current level is: **{user["level"]}**\n'
        embed.description += f'Your have **{user["exp"]}** experience points and you need `{EXP_AMOUNT[user["level"] + 1] - user["exp"]}` more experience points to level up.\n\n'
        embed.add_field(name='Card drop rates', value=RATES[user['level']][0], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='levelsinfo', aliases=['levels', 'li'])
    async def levelsinfo(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        embed = discord.Embed(title='Levels info', description='Below a list of all the things unlocked at each level.', colour=0xffcb05)
        for j in range(7):
            embed.add_field(name=f'Level {j} ({EXP_AMOUNT[j]} EXP)', value=RATES[j][1], inline=False)
        embed.set_footer(text='Page 1/3')
        message = await ctx.send(embed=embed)
        embeds = [embed]
        pages = 3
        for p in range(1, 3):
            next_page = discord.Embed(title='Levels info',
                                      description='Below a list of all the things unlocked at each level.',
                                      colour=0xffcb05)
            for j in range(7 * p, 7 * (p + 1)):
                next_page.add_field(name=f'Level {j} ({EXP_AMOUNT[j]} EXP)', value=RATES[j][1], inline=False)
            next_page.set_footer(text=f'Page {p + 1}/3')
            embeds.append(next_page)
        cur_page = 0

        await message.add_reaction('⬅')
        await message.add_reaction('➡')

        def check(r: discord.Reaction, u):
            return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=20, check=check)

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

    @commands.command(name='favpokemon', aliases=['favpoke', 'favp', 'fp'])
    async def favpokemon(self, ctx: commands.Context, *, name: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if name is None:
            await ctx.send(f'Sorry {ctx.author.mention}, you should provide a pokémon name. Please use the `help favpokemon` command to check the usage of this command.')
            return
        cards_filtered = sorted(list(cards.find({'name': {'$regex': f".*{name}.*", '$options': 'i'}})),
                                key=lambda d: d['_id'], reverse=False)
        if len(cards_filtered) == 0:
            await ctx.send(
                f'Sorry {ctx.author.mention}, that pokémon could not be found. It may not exist, or you may have misspelled its name.')
            return
        elif len(cards_filtered) == 1:
            poke_name = cards_filtered[0]['name']
            poke_id = cards_filtered[0]['_id']
            users.update_one(
                {'_id': str(ctx.author.id)},
                {'$set': {'favouritePokemon': poke_id}}
            )
            await ctx.send(f'{ctx.author.mention}, you successfully set **{poke_name.capitalize()}** as your favourite pokémon!')
        else:
            embed = discord.Embed(title='Pokémon Results',
                                  description=f'{ctx.author.mention}, please type the number that corresponds to the pokémon you are looking for.',
                                  colour=0xffcb05)
            field_text = ''
            if len(cards_filtered) < 10:
                for i in range(len(cards_filtered)):
                    poke_name = cards_filtered[i]['name']
                    field_text += f'{i + 1}. {poke_name}\n'
                embed.add_field(
                    name=f'Showing pokémons 1-{len(cards_filtered)}',
                    value=field_text)
                await ctx.send(embed=embed)
            else:
                for i in range(10):
                    poke_name = cards_filtered[i]['name']
                    field_text += f'{i + 1}. {poke_name}\n'
                embed.add_field(
                    name=f'Showing pokémons 1-10 of {len(cards_filtered)}',
                    value=field_text)
                message = await ctx.send(embed=embed)

                embeds = [embed]
                pages = (len(cards_filtered) // 10) + 1
                for p in range(1, pages):
                    next_page = discord.Embed(title='Card Results',
                                              description=f'{ctx.author.mention}, please type the number that corresponds to the pokémon you are looking for.',
                                              colour=0xffcb05)
                    field_text = ''
                    for i in range(10 * p,
                                   (10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)):
                        poke_name = cards_filtered[i]['name']
                        field_text += f'{i + 1}. {poke_name}\n'
                    next_page.add_field(
                        name=f'Showing pokémons {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)} of {len(cards_filtered)}',
                        value=field_text)
                    embeds.append(next_page)
                cur_page = 0

                await message.add_reaction('⬅')
                await message.add_reaction('➡')

                def check(r: discord.Reaction, u):
                    return u == ctx.author and str(r.emoji) in ['⬅', '➡'] and r.message == message

                while True:
                    tasks = [
                        asyncio.create_task(self.bot.wait_for('reaction_add', timeout=20, check=check), name='r'),
                        asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == ctx.author and int(
                            m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel, timeout=20),
                                            name='m')
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
                        poke_name = cards_filtered[int(msg.content) - 1]['name']
                        poke_id = cards_filtered[int(msg.content) - 1]['_id']
                        users.update_one(
                            {'_id': str(ctx.author.id)},
                            {'$set': {'favouritePokemon': poke_id}}
                        )
                        await ctx.send(
                            f'{ctx.author.mention}, you successfully set **{poke_name.capitalize()}** as your favourite pokémon!')
                        return


def setup(bot: commands.Bot):
    bot.add_cog(Profile(bot))
