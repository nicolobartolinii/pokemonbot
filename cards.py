import asyncio
import typing

from mongodb import *
from utils import *
from datetime import datetime


class Cards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='start')
    async def start(self, ctx: commands.Context):
        if len(list(users.find({'_id': str(ctx.author.id)}))) == 0:
            users.insert_one({
                '_id': str(ctx.author.id),
                'registeredAt': str(datetime.now().strftime('%m/%d/%Y, %H:%M:%S')),
                'cardsDropped': 0,
                'cardsGiven': 0,
                'cardsBurned': 0,
                'cardsGrabbed': 0,
                'cardsReceived': 0,
                'lastGrab': str((datetime.now() - timedelta(minutes=10, seconds=5)).strftime('%m/%d/%Y, %H:%M:%S')),
                'inventory': [],
                'wishlist': [],
                'wishWatching': '',
                'tags': {},
                'tagEmojis': {}
            })
            await ctx.send(f'Succesfully registered user {ctx.author.mention}.')
        else:
            await ctx.send(f'User {ctx.author.mention} already registered.')
            return

    @staticmethod
    def spawn_channel_check():
        async def predicate(ctx: commands.Context):
            spawn_channel_id = int(guilds.find_one({'_id': str(ctx.guild.id)})['spawnChannel'])
            return ctx.channel.id == spawn_channel_id
        return commands.check(predicate)

    @commands.command(name='spawn', aliases=['s'])
    @spawn_channel_check()
    @commands.cooldown(rate=1, per=1200, type=commands.BucketType.user)
    async def spawn(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            self.spawn.reset_cooldown(ctx)
            return
        guild = guilds.find_one({'_id': str(ctx.guild.id)})
        drops = list(db.cards.aggregate([{'$sample': {'size': 3}}]))
        ids = []
        for drop in drops:
            ids.append(drop['_id'])
        wish_watching = guild['wishWatching']
        watchers = []
        for wisher in wish_watching:
            watchers.append(users.find_one({'_id': str(wisher)}))
        to_ping = []
        for drop_id in ids:
            for watcher in watchers:
                if drop_id in watcher['wishlist']:
                    to_ping.append(int(watcher['_id']))
        temp_image_number = get_new_temp_image_number()
        imagecreation(ids).save(f'./temp{temp_image_number}.png', 'PNG')
        if len(to_ping) > 0:
            content = 'A card from your wishlist is spawning: '
            for ping in to_ping:
                content += f'{str(ctx.guild.get_member(ping).mention)} '
            await ctx.send(content=content)
        with open(f'./temp{temp_image_number}.png', 'rb') as f:
            picture = discord.File(f)
            drop = await ctx.send(content=f'{ctx.author.mention} is spawning 3 cards!', file=picture)
        await drop.add_reaction('1️⃣')
        await drop.add_reaction('2️⃣')
        await drop.add_reaction('3️⃣')
        users.update_one(
            {'_id': str(ctx.author.id)},
            {'$inc': {'cardsDropped': 3}}
        )
        grab1 = 'grab1'
        grab2 = 'grab2'
        grab3 = 'grab3'
        await asyncio.sleep(0.2)
        while True:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '1️⃣' and r.message.id == drop.id,
                    timeout=60
                ), name='grab1'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '2️⃣' and r.message.id == drop.id,
                    timeout=60
                ), name='grab2'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '3️⃣' and r.message.id == drop.id,
                    timeout=60
                ), name='grab3')
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
                await drop.edit(content="Spawn expired.")
                return

            if action == grab1:
                reaction, user = result
                grab_in_cooldown, time_str = is_grab_cooldown(user)
                if grab_in_cooldown:
                    await ctx.send(f'{user.mention}, you must wait `{time_str}` before grabbing another card.')
                    continue
                if not is_user_registered(user):
                    await ctx.send('You should first register an account using the `start` command.')
                    continue
                card_code = add_grabbed_card(ctx, user, drops[0])
                await ctx.send(f'{user.mention} grabbed the **{drops[0]["name"]}** card `{card_code}`!')
                grab1 = ' '
            elif action == grab2:
                reaction, user = result
                grab_in_cooldown, time_str = is_grab_cooldown(user)
                if grab_in_cooldown:
                    await ctx.send(f'{user.mention}, you must wait `{time_str}` before grabbing another card.')
                    continue
                if not is_user_registered(user):
                    await ctx.send('You should first register an account using the `start` command.')
                    continue
                card_code = add_grabbed_card(ctx, user, drops[1])
                await ctx.send(f'{user.mention} grabbed the **{drops[1]["name"]}** card `{card_code}`!')
                grab2 = ' '
            elif action == grab3:
                reaction, user = result
                grab_in_cooldown, time_str = is_grab_cooldown(user)
                if grab_in_cooldown:
                    await ctx.send(f'{user.mention}, you must wait `{time_str}` before grabbing another card.')
                    continue
                if not is_user_registered(user):
                    await ctx.send('You should first register an account using the `start` command.')
                    continue
                card_code = add_grabbed_card(ctx, user, drops[2])
                await ctx.send(f'{user.mention} grabbed the **{drops[2]["name"]}** card `{card_code}`!')
                grab3 = ' '
            if grab1 == grab2 == grab3:
                return

    @commands.command(name='collection', aliases=['c', 'cards'])
    async def collection(self, ctx: commands.Context, member: typing.Optional[discord.Member] = None, *, query: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose collection you are looking for is not registered. He should register an account using the `start` command.')
            return
        if member is None:
            member = ctx.author
        user = users.find_one({'_id': str(member.id)})
        cards_owned = user['inventory']
        cards_owned.reverse()
        embed = discord.Embed(title='Card Collection', description=f'Cards carried by {member.mention}.\n\n', colour=0xffcb05)
        if len(cards_owned) == 0:
            embed.description += 'Card collection is empty.'
            await ctx.send(embed=embed)
            return
        info_msg = await ctx.send(f"Retrieving {member.mention}'s collection...")
        cards_dict_list = []
        if query is not None:
            query_result = extrapolate_query(query)
            if query_result[0] == 0:
                cards_dict_list = sort_list_cards(member.id, cards_owned, query_result[1][0], query_result[2])
            elif query_result[0] == 1:
                filter_query = ' '.join(str(x) for x in query_result[1][1:])
                cards_dict_list = filter_cards(member.id, cards_owned, query_result[1][0], filter_query)
            elif query_result[0] == 2:
                filter_query = ' '.join(str(x) for x in query_result[3][1:])
                cards_dict_list = filter_cards(member.id, cards_owned, query_result[3][0], filter_query)
                cards_dict_list = sort_filtered_dict(cards_dict_list, query_result[1][0], query_result[2])
            elif query_result[0] == 3:
                cards_dict_list = sort_list_cards(member.id, cards_owned)
        else:
            cards_dict_list = sort_list_cards(member.id, cards_owned)
        if len(cards_dict_list) == 0:
            embed.description += 'The filter does not match any card in the collection or the query is wrong. Please use the `help collection` command to check the usage of advanced queries.'
            await ctx.send(embed=embed)
            return
        collection = []
        for card_dict in cards_dict_list:
            card_str = f'{card_dict["emoji"]} `{card_dict["code"]}` · `#{card_dict["print"]}` · `♡{str(card_dict["wishlists"])}` · `☆ {card_dict["rarity"]}` · {card_dict["set"]} · **{card_dict["name"]}**\n'
            collection.append(card_str)
        if len(collection) < 10:
            for i in range(len(collection)):
                embed.description += collection[i]
            embed.set_footer(text=f'Showing cards 1-{len(collection)}')
            await info_msg.delete()
            await ctx.send(embed=embed)
        elif len(collection) >= 10:
            for i in range(10):
                embed.description += collection[i]
            embed.set_footer(text=f'Showing cards 1-10 of {len(collection)}')
            await info_msg.delete()
            message = await ctx.send(embed=embed)

            embeds = [embed]
            pages = (len(collection) // 10) + 1
            for p in range(1, pages):
                next_page = discord.Embed(title='Card Collection', description=f'Cards carried by {member.mention}.\n\n', colour=0xffcb05)
                for i in range(10 * p, (10 * p + 10) if (10 * p + 10) < len(collection) else len(collection)):
                    next_page.description += collection[i]
                next_page.set_footer(text=f'Showing cards {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(collection) else len(collection)} of {len(collection)}')
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

    @commands.command(name='view', aliases=['v'])
    async def view(self, ctx: commands.Context, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if card_code is None:
            user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
            card_code = user_inventory[-1]
        card_code = card_code.upper()
        card_owner_docu = users.find_one({'inventory': {'$in': [str(card_code)]}})
        if card_owner_docu is None:
            await ctx.send(f'Sorry {ctx.author.mention}, that code is invalid.')
            return
        card_owner_id = card_owner_docu['_id']
        card_owner = self.bot.get_user(int(card_owner_id))
        grabbed_card = grabbed_cards.find_one({'_id': str(card_code)})
        card_id = grabbed_card['cardId']
        card_print = grabbed_card['print']
        generic_card = cards.find_one({'_id': str(card_id)})
        card_wishlists = generic_card['wishlists']
        card_set = generic_card['set']
        card_name = generic_card['name']
        card_rarity = generic_card['rarity']
        card_image = f'./imagesHigh/{card_id.split("-")[0]}_{card_id.split("-")[1]}_hires.png'
        embed = discord.Embed(title='Card Details', description=f'Owned by {card_owner.mention}\n\n', colour=0xffcb05)
        embed.description += f'`{card_code}` · `#{card_print}` · `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
        file = discord.File(card_image, filename='image.png')
        embed.set_image(url=f'attachment://image.png')
        await ctx.send(file=file, embed=embed)

    @commands.command(name='lookup', aliases=['lu'])
    async def lookup(self, ctx: commands.Context, *, card_name: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if card_name is None:
            user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
            card_code = user_inventory[-1]
            card_id = grabbed_cards.find_one({'_id': str(card_code)})['cardId']
            card = cards.find_one({'_id': str(card_id)})
            card_name = card['name']
            card_set = card['set']
            card_print = card['timesSpawned']
            card_rarity = card['rarity']
            card_artist = card['artist']
            await create_send_embed_lookup(ctx, card_name, card_set, card_print, card_rarity, card_id, card_artist)
            return
        else:
            cards_filtered = sorted(list(cards.find({'name': {'$regex': f".*{card_name}.*", '$options': 'i'}})), key=lambda d: d['wishlists'], reverse=True)
            if len(cards_filtered) == 0:
                await ctx.send(f'Sorry {ctx.author.mention}, that card could not be found. It may not exist, or you may have misspelled its name.')
                return
            elif len(cards_filtered) == 1:
                card_name = cards_filtered[0]['name']
                card_set = cards_filtered[0]['set']
                card_print = cards_filtered[0]['timesSpawned']
                card_rarity = cards_filtered[0]['rarity']
                card_id = cards_filtered[0]['_id']
                card_artist = cards_filtered[0]['artist']
                await create_send_embed_lookup(ctx, card_name, card_set, card_print, card_rarity, card_id, card_artist)
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
                else:  # TODO aggiungi footer con numero pagina e tasto per ingrandire l'immagine se fattibile
                    for i in range(10):
                        card_wishlists = cards_filtered[i]['wishlists']
                        card_name = cards_filtered[i]['name']
                        card_set = cards_filtered[i]['set']
                        card_rarity = cards_filtered[i]['rarity']
                        field_text += f'{i + 1}. `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n'
                    embed.add_field(
                        name=f'Showing cards 1-10 of {len(cards_filtered)}',
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
                            name=f'Showing cards {10 * p + 1}-{(10 * p + 10) if (10 * p + 10) < len(cards_filtered) else len(cards_filtered)} of {len(cards_filtered)}',
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
                            card_name = cards_filtered[int(msg.content) - 1]['name']
                            card_set = cards_filtered[int(msg.content) - 1]['set']
                            card_print = cards_filtered[int(msg.content) - 1]['timesSpawned']
                            card_rarity = cards_filtered[int(msg.content) - 1]['rarity']
                            card_id = cards_filtered[int(msg.content) - 1]['_id']
                            card_artist = cards_filtered[int(msg.content) - 1]['artist']
                            await create_send_embed_lookup(ctx, card_name, card_set, card_print, card_rarity,
                                                           card_id, card_artist)
                            return

                try:
                    msg = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == ctx.author and int(m.content) in range(1, len(cards_filtered) + 1) and m.channel == ctx.channel,
                        timeout=30
                    )
                except asyncio.TimeoutError:
                    return

                card_name = cards_filtered[int(msg.content) - 1]['name']
                card_set = cards_filtered[int(msg.content) - 1]['set']
                card_print = cards_filtered[int(msg.content) - 1]['timesSpawned']
                card_rarity = cards_filtered[int(msg.content) - 1]['rarity']
                card_id = cards_filtered[int(msg.content) - 1]['_id']
                card_artist = cards_filtered[int(msg.content) - 1]['artist']
                await create_send_embed_lookup(ctx, card_name, card_set, card_print, card_rarity, card_id, card_artist)

    @commands.command(name='cooldown', aliases=['cooldowns', 'cd'])
    async def cooldown(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        seconds_diff_spawn = int(self.spawn.get_cooldown_retry_after(ctx))
        grab_in_cooldown, time_str_grab = is_grab_cooldown(ctx.author)
        embed = discord.Embed(title='Cooldowns', description=f'Showing cooldowns for {ctx.author.mention}\n\n', colour=0xffcb05)
        if seconds_diff_spawn != 0.0:
            if seconds_diff_spawn >= 60:
                minutes = seconds_diff_spawn // 60
                time_str_spawn = f'{minutes} minutes'
            else:
                time_str_spawn = f'{seconds_diff_spawn} seconds'
            embed.description += f'**Spawn** is available in `{time_str_spawn}`\n'
        else:
            embed.description += f'**Spawn** is currently available\n'
        if grab_in_cooldown:
            embed.description += f'**Grab** is available in `{time_str_grab}`\n'
        else:
            embed.description += f'**Grab** is currently available\n'
        await ctx.send(embed=embed)

    # @commands.command(name='cardinfo', aliases=['ci'])
    # async def cardinfo(self, ctx: commands.Context, card_code: str = None):
    #     if not is_user_registered(ctx.author):
    #         await ctx.send('You should first register an account using the `start` command.')
    #         return
    #     user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
    #     if card_code is None:
    #         card_code = user_inventory[-1]
    #     card_code = card_code.upper()

    @spawn.error
    async def spawn_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            seconds_diff = round(error.retry_after)
            if seconds_diff >= 60:
                minutes = seconds_diff // 60
                time_str = f'{minutes} minutes'
            else:
                time_str = f'{seconds_diff} seconds'
            await ctx.send(f'{ctx.author.mention}, you must wait `{time_str}` before spawning more cards.')
        elif isinstance(error, commands.CheckFailure):
            spawn_channel_id = int(guilds.find_one({'_id': str(ctx.guild.id)})['spawnChannel'])
            await ctx.send(
                f'Sorry {ctx.author.mention}, the spawn channel for this server is: {ctx.guild.get_channel(spawn_channel_id).mention}.')


def setup(bot: commands.Bot):
    bot.add_cog(Cards(bot))
