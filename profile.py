from mongodb import *
import time


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='profile', aliases=['p'])
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if not is_user_registered(member or ctx.author):
            await ctx.send('The member whose collection you are looking for is not registered. He should register an account using the `start` command.')
            return
        if member is None:
            member = ctx.author
        user = users.find_one({'_id': str(member.id)})
        embed = discord.Embed(title='User details', description='', colour=0xffcb05)  # int(user['profileColor'], base=16))
        embed.set_author(name=member.name, icon_url=member.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)  # TODO sprite pokemon preferito OR avatar
        embed.description = f'Level · **{user["level"]}**/20\n'
        embed.description += f'Experience · **{user["exp"]}** (**{round(((user["exp"] - EXP_AMOUNT[user["level"]])/(EXP_AMOUNT[user["level"] + 1] - EXP_AMOUNT[user["level"]]))*100, 1)}%** to level **{user["level"] + 1}**)\n\n'
        embed.description += f'Favourite Pokémon · WIP\n\n'  # TODO
        embed.description += f'Cards in collection · **{len(user["inventory"])}**\n'
        embed.description += f'Last card grabbed · `{user["inventory"][-1]}`\n'
        embed.description += f'Cards grabbed · **{int(user["cardsGrabbed"])}**\n'
        embed.description += f'Cards spawned · **{int(user["cardsDropped"])}**\n'
        embed.description += f'Cards given · **{int(user["cardsGiven"])}**\n'
        embed.description += f'Cards received · **{int(user["cardsReceived"])}**\n'
        embed.description += f'Cards burned · **{int(user["cardsBurned"])}** (WIP)\n'
        embed.description += f'Minigames played · WIP\n'  # TODO
        embed.description += f'Minigames won · WIP\n'  # TODO
        playing_since = str(user['registeredAt'])
        date_registration = datetime.strptime(playing_since, '%m/%d/%Y, %H:%M:%S')
        date_registration_unix = time.mktime(date_registration.timetuple())
        embed.description += f'Playing since · <t:{str(int(date_registration_unix))}:F>'
        embed.add_field(name='Quick Inventory', value='WIP', inline=False)  # TODO
        await ctx.send(embed=embed)

    @commands.command(name='level', aliases=['lvl'])
    async def level(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        user = users.find_one({'_id': str(ctx.author.id)})
        embed = discord.Embed(title='Level details', description='', colour=0xffcb05)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.description += f'Your current level is: **{user["level"]}**\n'
        embed.description += f'Your have **{user["exp"]}** experience points and you need `{EXP_AMOUNT[user["level"] + 1] - user["exp"]}` more experience points to level up.\n\n'
        embed.add_field(name='Card drop rates', value=RATES[user['level']][0], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='levelsinfo', aliases=['levels', 'li'])
    async def levelsinfo(self, ctx: commands.Context):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        embed = discord.Embed(title='Levels info', description='', colour=0xffcb05)
        embed.description += f'Below a list of all the things unlocked at each level.'
        for j in range(21):
            embed.add_field(name=f'Level {j} ({EXP_AMOUNT[j]} EXP)', value=RATES[j][1], inline=False)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Profile(bot))
