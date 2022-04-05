from mongodb import *

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents().all()
default_prefixes = ['p!', 'p', 'p$']


async def determine_prefix(bot: commands.Bot, message: discord.Message):
    guild = message.guild
    if guild:
        custom_prefix = guilds.find_one({'_id': str(guild.id)})['customPrefix']
        return [custom_prefix, custom_prefix.upper()]
    else:
        return default_prefixes


bot = commands.Bot(command_prefix=determine_prefix, intents=intents)
bot.remove_command('help')

bot.load_extension('cards')
bot.load_extension('wishlist')
bot.load_extension('trades')
bot.load_extension('tags')
# bot.load_extension('profile')


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
async def channel(ctx: commands.Context, text_channel: discord.TextChannel = None):
    if text_channel is None:
        text_channel = ctx.channel
    guilds.update_one({'_id': str(ctx.guild.id)}, {'$set': {'spawnChannel': str(text_channel.id)}})
    await ctx.send(f'Spawn channel set to {text_channel.mention}')


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
        description=f'Spawn channel: {ctx.guild.get_channel(int(guild["spawnChannel"])).mention}\nPrefix: `{guild["customPrefix"]}`',
        colour=0xffcb05
    )
    await ctx.send(embed=embed)


@bot.command(name='help')
async def help(ctx: commands.Context, command: str = None):  # TODO da rifare per bene quando ci saranno più comandi
    embed = discord.Embed(title='Pokémon Collector Commands', description=f'Use `{bot.command_prefix}help <command>` to see more details about a particular command.', colour=0xffcb05)
    embed.add_field(name=f'`start`',
                    value='Register an account for Pokémon Collector bot.', inline=False)

    embed.add_field(name=f'`spawn`',
                    value='Aliases: `s`\nSpawn a set of cards in the current channel for anyone to grab.', inline=False)

    embed.add_field(name=f'`collection [user]`',
                    value="Aliases: `c`, `cards`\nView the card collection of yourself (in this case `user` can be omitted) or another user. [filtering WIP]", inline=False)

    embed.add_field(name=f'`view [code]`',
                    value='Aliases: `v`\nView your last card obtained (in this case `code` can be omitted) or a specific card with its code.', inline=False)

    embed.add_field(name=f'`lookup [search-query]`',
                    value='Aliases: `lu`\nLook up the details of a particular card using its name or a part of it. If `search-query` is omitted, you look up your last card obtained. [advanced search queries WIP]', inline=False)

    embed.add_field(name=f'`give <user> [card_code]`',
                    value='Aliases: `g`\nGive another user one of your cards. If `card_code` is omitted, you give to the user your last card obtained.',
                    inline=False)

    embed.add_field(name=f'`trade <user> <your_card_code> <user_card_code> `',
                    value='Trade one of your cards with another user for one of their cards. You can only trade one card at a time',
                    inline=False)

    embed.add_field(name=f'`createtag <tag_name> <emoji>`',
                    value='Aliases: `tagcreate`, `tagadd`, `ct`, `tc`\nCreate a new tag. The tag must contain only alphabetic characters, numbers, dashes or underscores. Custom emojis are highly discouraged as they may not be displayed on other servers.',
                    inline=False)

    embed.add_field(name=f'`deletetag <tag_name>`',
                    value='Aliases: `tagdelete`, `dy`, `td`\nDelete one of your tags. If any of your cards have this tag, the tag will be removed from those cards.',
                    inline=False)

    embed.add_field(name=f'`tag <tag_name> [card_code]`',
                    value='Aliases: `t`\nTag a card. If `card_code` is omitted, you tag your last card obtained.',
                    inline=False)

    embed.add_field(name=f'`untag [card_code]`',
                    value='Aliases: `ut`\nUntag a card. If `card_code` is omitted, you untag your last card obtained.',
                    inline=False)

    embed.add_field(name=f'`multitag <tag_name> <...card_codes>`',
                    value='Tag one or more cards. Card codes must be separated by spaces only and must be written in capital letters.',
                    inline=False)

    embed.add_field(name=f'`multiuntag <...card_codes>`',
                    value='Untag one or more cards. Card codes must be separated by spaces only and must be written in capital letters.',
                    inline=False)

    embed.add_field(name=f'`tags [user]`',
                    value='View the tag list of yourself (in this case `user` can be omitted) or another user.',
                    inline=False)

    embed.add_field(name=f'`renametag <old_tag_name> <new_tag_name>`',
                    value='Aliases: `tagrename`, `rnt`, `trn`\nRename one of your tags. The tag must contain only alphabetic characters, numbers, dashes or underscores.',
                    inline=False)

    embed.add_field(name=f'`tagemoji <tag_name> <new_emoji>`',
                    value='Aliases: `te`, `tagadd`, `ct`, `tc`\nChange the emoji on one of your tags. Custom emojis are highly discouraged as they may not be displayed on other servers.',
                    inline=False)

    embed.add_field(name=f'`wishlist [user]`',
                    value='Aliases: `w`, `wl`\nView the wishlist of yourself (in this case `user` can be omitted) or another user.', inline=False)

    embed.add_field(name=f'`wishadd <search-query>`',
                    value="Aliases: `wa`, `wadd`\nAdd a card to your wishlist. It's recommended to first use the `lookup` command to find the right card.", inline=False)

    embed.add_field(name=f'`wishremove`',
                    value='Aliases: `wr`, `wrem`\nRemove a card from your wishlist.', inline=False)

    embed.add_field(name=f'`wishwatch`',
                    value='Aliases: `ww`, `wishw`, `wwatch`\nSet the current channel as the channel where you will be mentioned if a card that spawns is in your wishlist.', inline=False)

    embed.add_field(name=f'`help`',
                    value='Shows this message.', inline=False)

    embed.add_field(name=f'`channel [channel]`',
                    value='Admin only command. Set the `spawn` channel. If `channel` is omitted, you set the current channel as the spawn channel.', inline=False)

    embed.add_field(name=f'`prefix <prefix>`',
                    value='Admin only command. Set the prefix for this server.', inline=False)

    embed.add_field(name=f'`server`',
                    value='Aliases: `serverinfo`, `si`\nAdmin only command. Shows the spawn channel and the prefix for this server.', inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
