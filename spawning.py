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
        # id_spawn = random.randint(1, 898)
        # print(id_spawn)
        # pokemon = pokemons.find_one({'_id': id_spawn})
        # print(pokemon)
        # pokemon_name = pokemon['name']
        # pokemon_artwork_url = pokemon['artwork']
        # embed = discord.Embed(
        #     title=f'Wild Pokémon appeared!',
        #     description=f'Type catch <pokémon-name> to catch it.'
        # )
        # embed.set_image(url=pokemon_artwork_url)
        # await ctx.send(embed=embed)
        #
        # check = lambda m: m.author == ctx.author and m.channel == ctx.channel
        #
        # try:
        #     catch = await self.bot.wait_for("message", check=check, timeout=60)
        # except asyncio.TimeoutError:
        #     await ctx.send(content=f'Oh no! The wild {pokemon_name.capitalize()} fled!')
        #     return
        #
        # if catch.content.lower() == f'catch {pokemon_name.lower()}':
        #     await ctx.send(f'{ctx.author.mention} captured the wild {pokemon_name.capitalize()}')
        #     return
        #
        # await ctx.send(f'Wrong name. The wild {pokemon_name.capitalize()} fled!')
        drops = list(db.cards.aggregate([{'$sample': {'size': 3}}]))
        images = []
        for drop in drops:
            images.append(drop['imageHigh'])
        print(images)
        image = imagecreation(images)
        with BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename='image.png'))


def setup(bot: commands.Bot):
    bot.add_cog(Spawning(bot))
