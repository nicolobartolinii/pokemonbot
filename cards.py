import asyncio
import time
import typing

from mongodb import *
from utils import *


def spawn_channel_check():
        async def predicate(ctx: commands.Context):
            spawn_channel_id = int(guilds.find_one({'_id': str(ctx.guild.id)})['spawnChannel'])
            return ctx.channel.id == spawn_channel_id
        return commands.check(predicate)


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
                'tagEmojis': {},
                'level': 0,
                'exp': 0,
                'itemInventory': [],
                'profileColor': 0xffcb05,
                'favouritePokemon': None,
                'coins': 0
            })
            await ctx.send(f'Succesfully registered user {ctx.author.mention}.')
        else:
            await ctx.send(f'User {ctx.author.mention} already registered.')
            return

    @commands.command(name='spawn', aliases=['s', 'S'])
    @spawn_channel_check()
    @commands.cooldown(rate=1, per=1200, type=commands.BucketType.user)
    async def spawn(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            self.spawn.reset_cooldown(ctx)
            return
        guild = guilds.find_one({'_id': str(ctx.guild.id)})
        user_level = users.find_one({'_id': str(ctx.author.id)})['level']
        rarities = [random.choice(PROB_RARITIES[user_level]) for _ in range(3)]
        # drops = list(db.cards.aggregate([{'$sample': {'size': 3}}]))
        drops = []
        for rarity in rarities:
            drops.append(list(cards.aggregate([{'$match': {'rarity': random.choice(CLASS_RARITIES[RARITY_ORDER_REV[rarity]])}}, {'$sample': {'size': 1}}]))[0])
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
            drop = await ctx.send(content=f'{ctx.author.mention} is spawning 3 cards! {ctx.author.mention} gained `1 EXP`!', file=picture)
        await add_exp(ctx, 1)
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
            if len(user_inventory) != 0:
                card_code = user_inventory[-1]
            else:
                await ctx.send(f'Sorry {ctx.author.mention}, your collection is empty.')
                return
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
            card_wishlists = card['wishlists']
            await create_send_embed_lookup(ctx, card_name, card_set, card_wishlists, card_print, card_rarity, card_id, card_artist)
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
                card_wishlists = cards_filtered[0]['wishlists']
                await create_send_embed_lookup(ctx, card_name, card_set, card_wishlists, card_print, card_rarity, card_id, card_artist)
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
                            card_wishlists = cards_filtered[int(msg.content) - 1]['wishlists']
                            await create_send_embed_lookup(ctx, card_name, card_set, card_wishlists, card_print, card_rarity,
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
                card_wishlists = cards_filtered[int(msg.content) - 1]['wishlists']
                await create_send_embed_lookup(ctx, card_name, card_set, card_wishlists, card_print, card_rarity, card_id, card_artist)

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

    @commands.command(name='cardinfo', aliases=['ci', 'cinfo'])
    async def cardinfo(self, ctx: commands.Context, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if card_code is None:
            user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
            if len(user_inventory) != 0:
                card_code = user_inventory[-1]
            else:
                await ctx.send(f'Sorry {ctx.author.mention}, your collection is empty.')
                return
        card_code = card_code.upper()
        card_owner_docu = users.find_one({'inventory': {'$in': [str(card_code)]}})
        if card_owner_docu is None:
            await ctx.send(f'Sorry {ctx.author.mention}, that code is invalid.')
            return
        card = grabbed_cards.find_one({'_id': str(card_code)})
        card_print = card['print']
        card_id = card['cardId']
        generic_card = cards.find_one({'_id': str(card_id)})
        card_wishlists = generic_card['wishlists']
        card_rarity = generic_card['rarity']
        card_set = generic_card['set']
        card_name = generic_card['name']
        owned_by = card['ownedBy']
        spawned_by = card['droppedBy']
        spawned_on = card['droppedOn']
        spawned_in = card['droppedIn']
        grabbed_by = card['grabbedBy']
        date_spawn = datetime.strptime(spawned_on, '%m/%d/%Y, %H:%M:%S')
        date_spawn_unix = time.mktime(date_spawn.timetuple())
        embed = discord.Embed(title='Card Details', description=f'`{card_code}` · `#{card_print}` · `♡{str(card_wishlists)}` · `☆ {card_rarity}` · {card_set} · **{card_name}**\n\n', colour=0xffcb05)
        embed.description += f'Spawned on <t:{str(int(date_spawn_unix))}:F>\n'
        embed.description += f'Spawned in server ID: {spawned_in}\n'
        embed.description += f'Spawned by <@{spawned_by}>\n'
        embed.description += f'Grabbed by <@{grabbed_by}>\n'
        embed.description += f'Owned by <@{owned_by}>\n\n'
        embed.description += f'Rarity class: **{RARITIES[card_rarity]}**'
        card_image = f'./imagesLow/{card_id.split("-")[0]}_{card_id.split("-")[1]}.png'
        file = discord.File(card_image, filename='image.png')
        embed.set_thumbnail(url='attachment://image.png')
        await ctx.send(file=file, embed=embed)

    @commands.command(name='burn', aliases=['b'])
    async def burn(self, ctx: commands.Context, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_burning = users.find_one({'_id': str(ctx.author.id)})
        if len(user_burning["inventory"]) == 0:
            await ctx.send(f'Sorry {ctx.author.mention}, your card collection is empty.')
            return
        if card_code is None:
            card_code = user_burning['inventory'][-1]
        card_code = card_code.upper()
        if card_code not in user_burning['inventory']:
            await ctx.send(f'Sorry {ctx.author.mention}, that card code is invalid.')
            return
        grabbed_card = grabbed_cards.find_one({'_id': card_code})
        card_id = grabbed_card['cardId']
        card = cards.find_one({'_id': card_id})
        embed = discord.Embed(title='Burn Card', description=f'{ctx.author.mention}, you will receive:\n\n', colour=0xffcb05)
        rewards = det_rewards(card_code)
        embed.description += f'💫 **{rewards[0]}** Exp\n🪙 **{rewards[1]}** Coins'
        embed.set_thumbnail(url=card['imageLow'])
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('❌')
        await msg.add_reaction('🔥')

        try:
            r, u = await self.bot.wait_for('reaction_add', timeout=30, check=lambda reaction, user: user == ctx.author and str(reaction.emoji) in '❌🔥')
        except asyncio.TimeoutError:
            return
        if str(r.emoji) == '❌':
            embed.description += '\n\n**Card burning has been canceled.**'
            embed.colour = 0xfd0111
            await msg.edit(embed=embed)
            return
        elif str(r.emoji) == '🔥':
            await burn_card(ctx, user_burning, rewards, card_code)
            embed.description += '\n\n**The card has been burned.**'
            embed.colour = 0x35ff42
            await msg.edit(embed=embed)

    @commands.command(name='tagburn', aliases=['tb', 'tagb', 'tburn'])
    async def tagburn(self, ctx: commands.Context, tag_name: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_burning = users.find_one({'_id': str(ctx.author.id)})
        user_inventory = user_burning['inventory']
        if len(user_inventory) == 0:
            await ctx.send(f'Sorry {ctx.author.mention}, your card collection is empty.')
            return
        if tag_name is None:
            await ctx.send(f'Sorry {ctx.author.mention}, you should provide a tag name.')
            return
        tag_name = tag_name.lower()
        try:
            tagged_cards = user_burning['tags'][tag_name]
        except KeyError:
            await ctx.send(f'Sorry {ctx.author.mention}, that tag does not exists.')
            return
        rewards = [0, 0]
        single_rewards = []
        for card in tagged_cards:
            card_reward = det_rewards(card)
            single_rewards.append(card_reward)
            rewards[0] += card_reward[0]
            rewards[1] += card_reward[1]
        embed = discord.Embed(title='Burn Tagged Cards', description=f'{ctx.author.mention}, you will receive:\n\n',
                              colour=0xffcb05)
        embed.description += f'💫 **{rewards[0]}** Exp\n🪙 **{rewards[1]}** Coins\n\n**You are burning the {round((len(tagged_cards)/len(user_inventory)) * 100, 1)}% of your collection. Please, before confirming, check the cards you are burning using the** `collection f:tag:{tag_name}` **command.**'
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('❌')
        await msg.add_reaction('🔥')

        try:
            r, u = await self.bot.wait_for('reaction_add', timeout=30,
                                           check=lambda reaction, user: user == ctx.author and str(
                                               reaction.emoji) in '❌🔥')
        except asyncio.TimeoutError:
            return
        if str(r.emoji) == '❌':
            embed.description += '\n\n**Card burning has been canceled.**'
            embed.colour = 0xfd0111
            await msg.edit(embed=embed)
            return
        elif str(r.emoji) == '🔥':
            await msg.add_reaction('✅')
            try:
                r, u = await self.bot.wait_for('reaction_add', timeout=10,
                                               check=lambda reaction, user: user == ctx.author and str(
                                                   reaction.emoji) == '✅')
            except asyncio.TimeoutError:
                return
            if str(r.emoji) == '✅':
                for j in range(len(tagged_cards)):
                    await burn_card(ctx, user_burning, single_rewards[j], tagged_cards[j])
                embed.description += '\n\n**Cards have been burned.**'
                embed.colour = 0x35ff42
                await msg.edit(embed=embed)

    @commands.command(name='multiburn', aliases=['mb'])
    async def multiburn(self, ctx: commands.Context, *codes):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user_burning = users.find_one({'_id': str(ctx.author.id)})
        user_inventory = user_burning['inventory']
        codes = [code.upper() for code in codes]
        for code in codes:
            for invalid_char in [',', '@', '#', '.', '-', ':', ';', '_', '!', '$', 'ù', 'à', 'è', 'ì', 'ò', '?', '^']:
                if invalid_char in code:
                    await ctx.send(f'{ctx.author.mention}, at least one of those card codes is wrong. Please use the `help` command to check the correct usage of commands.')
                    return
            if code not in user_inventory:
                await ctx.send(f'{ctx.author.mention}, you are not the owner of at least one of those cards.')
                return
        rewards = [0, 0]
        single_rewards = []
        for card in codes:
            card_reward = det_rewards(card)
            single_rewards.append(card_reward)
            rewards[0] += card_reward[0]
            rewards[1] += card_reward[1]
        embed = discord.Embed(title='Burn Tagged Cards', description=f'{ctx.author.mention}, you will receive:\n\n',
                              colour=0xffcb05)
        embed.description += f'💫 **{rewards[0]}** Exp\n🪙 **{rewards[1]}** Coins\n\n**You are burning the {round((len(codes) / len(user_inventory)) * 100, 1)}% of your collection. Please, before confirming, check if the cards you have selected are the ones you want to burn.**'
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('❌')
        await msg.add_reaction('🔥')

        try:
            r, u = await self.bot.wait_for('reaction_add', timeout=30,
                                           check=lambda reaction, user: user == ctx.author and str(
                                               reaction.emoji) in '❌🔥')
        except asyncio.TimeoutError:
            return
        if str(r.emoji) == '❌':
            embed.description += '\n\n**Card burning has been canceled.**'
            embed.colour = 0xfd0111
            await msg.edit(embed=embed)
            return
        elif str(r.emoji) == '🔥':
            await msg.add_reaction('✅')
            try:
                r, u = await self.bot.wait_for('reaction_add', timeout=10,
                                               check=lambda reaction, user: user == ctx.author and str(
                                                   reaction.emoji) == '✅')
            except asyncio.TimeoutError:
                return
            if str(r.emoji) == '✅':
                for j in range(len(codes)):
                    await burn_card(ctx, user_burning, single_rewards[j], codes[j])
                embed.description += '\n\n**Cards have been burned.**'
                embed.colour = 0x35ff42
                await msg.edit(embed=embed)

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
