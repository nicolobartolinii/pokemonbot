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
        if len(list(users.find({'_id': str(ctx.author.id)}))) != 0:
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

        check = lambda r, u: str(r.emoji) in "1️⃣2️⃣3️⃣"

        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            await drop.edit(content="Spawn expired.")
            return

        if str(reaction.emoji) == "1️⃣":
            pass
        if str(reaction.emoji) == "2️⃣":
            pass
        if str(reaction.emoji) == "3️⃣":
            pass


def setup(bot: commands.Bot):
    bot.add_cog(Spawning(bot))
