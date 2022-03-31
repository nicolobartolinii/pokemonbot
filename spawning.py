import asyncio
import time

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

        timeout = 60

        timeout_start = time.time()

        while time.time() < timeout_start + timeout:
            @commands.Cog.listener()
            async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
                if not isinstance(user, discord.User) or str(reaction.emoji) not in "1️⃣2️⃣3️⃣":
                    return
                if str(reaction.emoji) == "1️⃣":
                    add_grabbed_card(ctx, user, drops[0])
                if str(reaction.emoji) == "2️⃣":
                    add_grabbed_card(ctx, user, drops[1])
                if str(reaction.emoji) == "3️⃣":
                    add_grabbed_card(ctx, user, drops[2])


def setup(bot: commands.Bot):
    bot.add_cog(Spawning(bot))
