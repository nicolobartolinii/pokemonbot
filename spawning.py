import asyncio

import discord
from discord.ext import commands
from pymongo import MongoClient
from mongodb import *
import random
from utils import *
from io import BytesIO


class Spawning(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='spawn')
    async def spawn(self, ctx: commands.Context):
        drops = list(db.cards.aggregate([{'$sample': {'size': 3}}]))
        ids = []
        for drop in drops:
            ids.append(drop['_id'])
        print(ids)
        imagecreation(ids).save('./temp.png', 'PNG')
        with open('./temp.png', 'wb') as f:
            picture = discord.File(f)
            await ctx.send(file=picture)


def setup(bot: commands.Bot):
    bot.add_cog(Spawning(bot))
