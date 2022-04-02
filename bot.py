from mongodb import *

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents().all()
default_prefixes = ['p!', 'p', 'p$']


async def determine_prefix(bot: commands.Bot, message: discord.Message):
    guild = message.guild
    if guild:
        return guilds.find_one({'_id': str(guild.id)})['customPrefix']
    else:
        return default_prefixes


bot = commands.Bot(command_prefix=determine_prefix, intents=intents)
bot.load_extension('spawning')
bot.load_extension('wishlist')


@bot.event
async def on_guild_join(guild: discord.Guild):
    res = guilds.find_one({'_id': str(guild.id)})
    if res is None:
        guilds.insert_one({
            '_id': str(guild.id),
            'spawnChannel': str(guild.text_channels[0].id),
            'customPrefix': 'p!',
            'wishWatching': []
        })
        text_channel = guild.text_channels[0]
        embed = discord.Embed(
            title='Welcome to Pokémon Collector Bot!',  # TODO NOME DA RIVEDERE
            description='Thank you for adding Pokémon Collector Bot to your server! Before you can start playing, have a server admin use the command `p!channel` to set the Pokémon cards spawn channel.',
            colour=0xffcb05
        )
        await text_channel.send(embed=embed)


@bot.command(name='channel')
@commands.has_guild_permissions(administrator=True)
async def channel(ctx: commands.Context, text_channel: discord.TextChannel):
    guilds.update_one({'_id': str(ctx.guild.id)}, {'$set': {'spawnChannel': str(text_channel.id)}})


@bot.command(name='prefix')
@commands.has_guild_permissions(administrator=True)
@commands.guild_only()
async def prefix(ctx: commands.Context, *, custom_prefix: str = 'p!'):
    guilds.update_one({'_id': str(ctx.guild.id)}, {'$set': {'customPrefix': custom_prefix}})
    await ctx.send(f"Prefix set to `{custom_prefix}`!")


@bot.command(name='server', aliases=['serverinfo', 'si'])
@commands.has_guild_permissions(administrator=True)
async def server(ctx: commands.Context):
    guild = guilds.find_one({'_id': str(ctx.guild.id)})
    embed = discord.Embed(
        title=f'Server settings for {ctx.guild.name}',
        description=f'Spawn channel: {ctx.guild.get_channel(guild["spawnChannel"]).mention}\nPrefix: `{guild["customPrefix"]}`',
        colour=0xffcb05
    )
    await ctx.send(embed=embed)


@bot.command(name='help')
async def help(ctx: commands.Context):  # TODO da rifare per bene quando ci saranno più comandi
    embed = discord.Embed(title='Pokémon Collector Commands', colour=0xffcb05)
    embed.add_field(name=f'`spawn`', value='Aliases: `s`\nSpawn a set of cards in the current channel for anyone to grab.', inline=False)
    await ctx.send(embed=embed)



bot.run(TOKEN)
