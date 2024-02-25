from mongodb import *
import os
import asyncio

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


async def load_extensions():
    bot.load_extension('cards')
    bot.load_extension('wishlist')
    bot.load_extension('trades')
    bot.load_extension('tags')
    bot.load_extension('profile')
    bot.load_extension('minigames')


async def main():
    await load_extensions()
    await bot.start(TOKEN)


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
async def server(ctx: commands.Context):
    guild = guilds.find_one({'_id': str(ctx.guild.id)})
    embed = discord.Embed(
        title=f'Server settings for {ctx.guild.name}',
        description=f'Spawn channel: {ctx.guild.get_channel(int(guild["spawnChannel"])).mention}\nPrefix: `{guild["customPrefix"]}`',
        colour=0xffcb05
    )
    await ctx.send(embed=embed)


@bot.command(name='help')
async def help(ctx: commands.Context, command: str = None):
    print('sono in help')
    if command is None:
        embed = discord.Embed(title='Pokémon Collector Commands',
                              description='Use `help <command>` to see more details about a particular command.',
                              colour=0xffcb05)
        embed.add_field(name='**📜Cards**', value='`burn`, `collection`, `multiburn`, `spawn`, `tagburn`, `view`',
                        inline=True)
        embed.add_field(name='**🏷Tags**',
                        value='`createtag`, `deletetag`, `renametag`, `multitag`, `multiuntag`, `tag`, `tagemoji`, `tags`, `untag`',
                        inline=True)
        embed.add_field(name='**ℹInfo**', value='`cardinfo`, `cooldown`, `help`, `lookup`, `server`', inline=True)
        embed.add_field(name='**✨Wishlist**', value='`wishadd`, `wishlist`, `wishremove`, `wishwatch`', inline=True)
        embed.add_field(name='**🔄Trades**', value='`give`, `trade`', inline=True)
        embed.add_field(name='**👤Profile**', value='`coins`, `favpokemon`, `level`, `levelsinfo`, `start`, `profile`',
                        inline=True)
        embed.add_field(name='**⚙Admin/Settings**', value='`channel`, `prefix`', inline=True)
        await ctx.send(embed=embed)
    elif command == 'collection' or command == 'c' or command == 'cards':
        embed = discord.Embed(title='Command Details: `collection [user] [query]`',
                              description='Aliases: `c`, `cards`\n\nView the card collection of yourself (in this case `user` can be omitted) or another user.\n\nThe `query` parameter is used to sort or filter the collection: please use `help collection-advanced` for more informations.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'collection-advanced':
        await ctx.send(content="""
```asciidoc
General info about usage
------------------------
Command arguments:
[collection [user(optional)] [query]]

Collection sorting is done using in the query:
------------------------
- order:
- order=
- o:
- o=
followed by one of the following parameters:
- name or n (sorts by names in alphabetical order)
- set or s (sorts by set names in alphabetical order)
- code or n (sorts by card codes in alphabetical order)
- wishlist or wl (sorts by wishlists in descending order)
- print or p (sorts by print numbers in ascending order)
- date or d (sorts by date obtained from newest to oldest) [default]
- rarity (sorts by rarity from the rarest to the least rare)
Those parameters can be followed by the keyword reverse or the letter r to invert the sorting order.

Collection filtering is done using in the query:
------------------------
- filter:
- filter=
- f:
- f=
followed by one of the following selectors and parameters:
- name:<card_name> (shows all cards that have <card_name> in their name) (name or n)
- set:<set_name> (shows all cards that have <set_name> in their set name) (set or s)
- wishlist:<number> (shows all cards that are in <number> wishlists) (wishlist or wl)
- print:<number> (shows all cards that have <number> print) (print or p)
- rarity:<rarity_name> (shows all cards that have <rarity_name> in their rarity) (rarity)
- spawner:<user_id> (shows all cards that have been spawned by <user_id>)
- grabber:<user_id> (shows all cards that have been grabbed by <user_id>)
- tag:<tag_name> (shows all cards that have been tagged with <tag_name>) (tag or t)

Other
------------------------
- Filtering and sorting can be combined in the same command
- For examples of usage use the help collection-ex command
```
        """)
    elif command == 'collection-ex':
        pass
    elif command == 'createtag' or command == 'tagcreate' or command == 'tagadd' or command == 'ct' or command == 'tc':
        embed = discord.Embed(title='Command Details: `createtag <tag_name> <emoji>`',
                              description='**Aliases**: `tagcreate`, `tagadd`, `ct`, `tc`\n\nCreate a new tag. The tag must contain only alphabetic characters, numbers, dashes or underscores. Custom emojis are highly discouraged as they may not be displayed on other servers.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'spawn' or command == 's':
        embed = discord.Embed(title='Command Details: `spawn`',
                              description='**Aliases**: `s`\n\nSpawn a set of cards in the current channel for anyone to grab. This command has a cooldown of 20 minutes.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'view' or command == 'v':
        embed = discord.Embed(title='Command Details: `view [code]`',
                              description='**Aliases**: `v`\n\nView your last card obtained (in this case `code` can be omitted) or a specific card with its code.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'deletetag' or command == 'tagdelete' or command == 'dt' or command == 'td':
        embed = discord.Embed(title='Command Details: `deletetag <tag_name>`',
                              description='**Aliases**: `tagdelete`, `dt`, `td`\n\nDelete one of your tags. If any of your cards have this tag, the tag will be removed from those cards.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'renametag' or command == 'tagrename' or command == 'rnt' or command == 'trn':
        embed = discord.Embed(title='Command Details: `renametag <old_tag_name> <new_tag_name>`',
                              description='**Aliases**: `tagrename`, `rnt`, `trn`\n\nRename one of your tags. The tag must contain only alphabetic characters, numbers, dashes or underscores.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'multitag':
        embed = discord.Embed(title='Command Details: `multitag <tag_name> <...card_codes>`',
                              description='Tag one or more cards. Card codes must be separated by spaces only and should be written in capital letters.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'multiuntag':
        embed = discord.Embed(title='Command Details: `multiuntag <...card_codes>`',
                              description='Untag one or more cards. Card codes must be separated by spaces only and should be written in capital letters.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'tag' or command == 't':
        embed = discord.Embed(title='Command Details: `tag <tag_name> [card_code]`',
                              description='**Aliases**: `t`\n\nTag a card. If `card_code` is omitted, you tag your last card obtained.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'tagemoji' or command == 'te':
        embed = discord.Embed(title='Command Details: `tagemoji <tag_name> <new_emoji>`',
                              description='**Aliases**: `te`\n\nChange the emoji on one of your tags. Custom emojis are highly discouraged as they may not be displayed on other servers.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'tags':
        embed = discord.Embed(title='Command Details: `tags [user]`',
                              description='View the tag list of yourself (in this case `user` can be omitted) or another user.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'untag' or command == 'ut':
        embed = discord.Embed(title='Command Details: `untag [card_code]`',
                              description='**Aliases**: `ut`\n\nUntag a card. If `card_code` is omitted, you untag your last card obtained.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'cardinfo' or command == 'ci' or command == 'cinfo':
        embed = discord.Embed(title='Command Details: `cardinfo [card_code]`',
                              description='View the detailed information of a particular card. If `card_code` is omitted, you view the details of your last card obtained. ',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'cooldown' or command == 'cd' or command == 'cooldowns':
        embed = discord.Embed(title='Command Details: `cooldown`',
                              description='**Aliases**: `cd`, `cooldowns`\n\nView current grab and spawn cooldowns for yourself.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'help':
        embed = discord.Embed(title='Command Details: `help [command]`',
                              description='View the list of the commands (in this case `command` can be omitted) or the details for a particular command.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'lookup' or command == 'lu':
        embed = discord.Embed(title='Command Details: `lookup [card_name]`',
                              description='**Aliases**: `lu`\n\nLook up the details of a particular card using its name or a part of it. If `card_name` is omitted, you look up your last card obtained.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'profile' or command == 'p':
        embed = discord.Embed(title='Command Details: `profile [user]`',
                              description='**Aliases**: `p`\n\nView the profile of yourself (in this case `user` can be omitted) or another user.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'level' or command == 'lvl':
        embed = discord.Embed(title='Command Details: `level`',
                              description='**Aliases**: `lvl`\n\nView the details of your experience level.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'levelsinfo' or command == 'levels' or command == 'li':
        embed = discord.Embed(title='Command Details: `levelsinfo`',
                              description='**Aliases**: `levels`, `li`\n\nView the list of all things unlocked at each level.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'favpokemon' or command == 'favpoke' or command == 'favp' or command == 'fp':
        embed = discord.Embed(title='Command Details: `favpokemon <pokémon_name>`',
                              description='**Aliases**: `favpoke`, `favp`, `fp`\n\nSet a pokémon as your favourite pokémon. This pokemon will appear in your profile (it can sometimes appear shiny) and WIP.\nUse `None` as pokémon name to delete your favourite pokémon.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'wishadd' or command == 'wa' or command == 'wadd':
        embed = discord.Embed(title='Command Details: `wishadd <card_name>`',
                              description="**Aliases**: `wa`, `wadd`\n\nAdd a card to your wishlist. It's recommended to first use the `lookup` command to find the right card.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'wishlist' or command == 'w' or command == 'wl':
        embed = discord.Embed(title='Command Details: `wishlist [user]`',
                              description="**Aliases**: `w`, `wl`\n\nView the wishlist of yourself (in this case `user` can be omitted) or another user.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'wishremove' or command == 'wr' or command == 'wrem':
        embed = discord.Embed(title='Command Details: `wishremove <card_name>`',
                              description="**Aliases**: `wr`, `wrem`\n\nRemove a card from your wishlist.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'wishwatch' or command == 'ww' or command == 'wishw' or command == 'wwatch':
        embed = discord.Embed(title='Command Details: `wishwatch`',
                              description="**Aliases**: `ww`, `wishw`, `wwatch`\n\nSet the current channel as the channel where you will be mentioned if a card that spawns is in your wishlist.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'give' or command == 'g':
        embed = discord.Embed(title='Command Details: `give <user> [card_code]`',
                              description="**Aliases**: `g`\n\nGive another user one of your cards. If `card_code` is omitted, you give to the user your last card obtained.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'trade':
        embed = discord.Embed(title='Command Details: `trade <user> <your_card_code> <user_card_code>`',
                              description="Trade one of your cards with another user for one of their cards. You can only trade one card at a time.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'start':
        embed = discord.Embed(title='Command Details: `start`',
                              description="Register an account for Pokémon Collector bot.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'channel':
        embed = discord.Embed(title='Command Details: `channel [channel]`',
                              description="Admin only command. Set the `spawn` channel. If `channel` is omitted, you set the current channel as the spawn channel.",
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'prefix':
        embed = discord.Embed(title='Command Details: `prefix <prefix>`',
                              description='Admin only command. Set the prefix for this server.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'server' or command == 'serverinfo' or command == 'si':
        embed = discord.Embed(title='Command Details: `server`',
                              description='**Aliases**: `serverinfo`, `si`\n\nShows the spawn channel and the prefix for this server.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'burn' or command == 'b':
        embed = discord.Embed(title='Command Details: `burn [card_code]`',
                              description='**Aliases**: `b`\n\nBurn a card and collect its resources. If `card_code` is omitted, you burn your last obtained card.\n\nBurning cards is useful to obtain **experience points** and other resources.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'multiburn' or command == 'mb':
        embed = discord.Embed(title='Command Details: `multiburn <...card_codes>`',
                              description='**Aliases**: `mb`\n\nBurn more than one cards and collect their resources. Card codes must be separated by spaces only and should be written in capital letters.\n\nBurning cards is useful to obtain **experience points** and other resources.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'tagburn' or command == 'tb' or command == 'tagb' or command == 'tburn':
        embed = discord.Embed(title='Command Details: `tagburn <tag_name>`',
                              description='**Aliases**: `tb`, `tagb`, `tburn`\n\nBurn all the cards in your collection that are tagged with `tag_name` and collect their resources.\n\nBurning cards is useful to obtain **experience points** and other resources.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    elif command == 'coins' or command == 'money' or command == 'balance' or command == 'cash':
        embed = discord.Embed(title='Command Details: `coins`',
                              description='**Aliases**: `money`, `balance`\n\nView the amount of your coins.\n\nCoins can be spent in the `shop` to buy card packs and other things.',
                              colour=0xffcb05)
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            f'Sorry {ctx.author.mention}, that is not a valid command. Please use the `help` command to see the list of available commands.')


@bot.command(name='aggiornaroba')
@commands.is_owner()
async def aggiornaroba(ctx: commands.Context):
    # general_bot_settings_db = general_bot_settings.find_one({'_id': 0})
    # free_codes = general_bot_settings_db['freeCodes']
    # for code in free_codes:
    #     card = grabbed_cards.find_one({'_id': str(code)})
    #     if card is not None:
    #         await ctx.send(f'{code}')
    ids = list(grabbed_cards.find({}, {'_id': 1}))
    for idd in ids:
        ris = list(users.find({'inventory': str(idd['_id'])}))
        if len(ris) > 1:
            await ctx.send(f'doppione {idd["_id"]}')
        elif len(ris) == 0:
            await ctx.send(f'nullo {idd["_id"]}')
        elif len(ris) == 1:
            print(f'{idd} OK')
        elif ris is None:
            await ctx.send(f'None {idd["_id"]}')


asyncio.run(main())
