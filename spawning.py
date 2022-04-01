import asyncio
import discord
from discord.ext import commands
from pymongo import MongoClient
from mongodb import *
import random
from utils import *
from io import BytesIO
from datetime import datetime


class Spawning(commands.Cog):
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
                'lastGrab': '',
                'inventory': []
            })
            await ctx.send(f'Succesfully registered user {ctx.author.mention}.')
        else:
            await ctx.send(f'User {ctx.author.mention} already registered.')
            return

    @commands.command(name='spawn')
    async def spawn(self, ctx: commands.Context):
        if len(list(users.find({'_id': str(ctx.author.id)}))) == 0:
            await ctx.send('You should first register an account using the `p$start` command.')
            return
        drops = list(db.cards.aggregate([{'$sample': {'size': 3}}]))
        ids = []
        for drop in drops:
            ids.append(drop['_id'])
        print(ids)
        imagecreation(ids).save('./temp.png', 'PNG')
        with open('./temp.png', 'rb') as f:
            picture = discord.File(f)
            drop = await ctx.send(content=f'{ctx.author.mention} is spawning 3 cards!', file=picture)
        await drop.add_reaction('1️⃣')
        await drop.add_reaction('2️⃣')
        await drop.add_reaction('3️⃣')
        grab1 = 'grab1'
        grab2 = 'grab2'
        grab3 = 'grab3'
        await asyncio.sleep(0.3)
        while True:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '1️⃣',
                    timeout=60
                ), name='grab1'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '2️⃣',
                    timeout=60
                ), name='grab2'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: isinstance(u, discord.Member) and str(r.emoji) in '3️⃣',
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

            # TODO check che uno abbia fatto p$start

            if action == grab1:
                reaction, user = result
                grab_in_cooldown, time_str = is_grab_cooldown(user)
                if grab_in_cooldown:
                    await ctx.send(f'{user.mention}, you must wait `{time_str}` before grabbing another card.')
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
                card_code = add_grabbed_card(ctx, user, drops[1])
                await ctx.send(f'{user.mention} grabbed the **{drops[1]["name"]}** card `{card_code}`!')
                grab2 = ' '
            elif action == grab3:
                reaction, user = result
                grab_in_cooldown, time_str = is_grab_cooldown(user)
                if grab_in_cooldown:
                    await ctx.send(f'{user.mention}, you must wait `{time_str}` before grabbing another card.')
                    continue
                card_code = add_grabbed_card(ctx, user, drops[2])
                await ctx.send(f'{user.mention} grabbed the **{drops[2]["name"]}** card `{card_code}`!')
                grab3 = ' '
            if grab1 == grab2 == grab3:
                return

    @commands.command(name='collection', aliases=['c'])
    async def collection(self, ctx: commands.Context, member: discord.Member = None):  # TODO altri argomenti per filtrare la collection
        if member is None:
            member = ctx.author
        user = users.find_one({'_id': str(member.id)})
        cards_owned = user['inventory']
        embed = discord.Embed(title='Card Collection', description=f'Cards carried by {member.mention}.\n\n')
        if len(cards_owned) == 0:
            embed.description += 'Card collection is empty.'
            await ctx.send(embed=embed)
            return
        collection = []
        for card_code in cards_owned:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            print_num = card_info['print']
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            set_name = generic_card['set']
            card_name = generic_card['name']
            card_str = f'`{card_code}` · `#{print_num}` · {set_name} · **{card_name}**\n'
            collection.append(card_str)
        i = 1
        for card in collection:
            embed.description += card
            i += 1
            if i == 11:
                break
        embed.set_footer(text=f'Showing cards 1-10 of {len(cards_owned)}')
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Spawning(bot))
