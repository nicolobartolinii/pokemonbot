import asyncio

import discord.ext.commands

from mongodb import *


class Trades(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='give', aliases=['g'])
    async def give(self, ctx: commands.Context, member: discord.Member, card_code: str = None):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if ctx.guild.get_member(member.id) is None:
            await ctx.send(f'User not found.')
            return
        if not is_user_registered(member):
            await ctx.send('The member you want to give the card to is not registered. He should register an account using the `start` command.')
            return
        if ctx.author.id == member.id:
            await ctx.send(f'Sorry {ctx.author.mention}, you cannot give cards to yourself.')
            return
        user_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
        if card_code is None:
            card_code = user_inventory[-1]
        card_code = card_code.upper()
        if card_code not in user_inventory:
            await ctx.send(f'{ctx.author.mention}, you do not have this card.')
            return
        giving = grabbed_cards.find_one({'_id': str(card_code)})
        card_id = giving['cardId']
        card_print = giving['print']
        generic_card = cards.find_one({'_id': str(card_id)})
        card_wishlists = generic_card['wishlists']
        card_set = generic_card['set']
        card_name = generic_card['name']
        card_rarity = generic_card['rarity']
        card_image = f'./imagesHigh/{card_id.split("-")[0]}_{card_id.split("-")[1]}_hires.png'
        embed = discord.Embed(title='Card Transfer', description=f'{ctx.author.mention}`→`{member.mention}\n\n', colour=0xffcb05)
        embed.description += f'`{card_code}` · `#{card_print}` · `♡{str(card_wishlists)}` · `☆ {str(card_rarity)}` · {card_set} · **{card_name}**\n'
        file = discord.File(card_image, filename='image.png')
        embed.set_image(url=f'attachment://image.png')
        give_msg = await ctx.send(file=file, embed=embed)
        await give_msg.add_reaction('❌')
        await give_msg.add_reaction('✅')
        while True:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: u.id == ctx.author.id and str(r.emoji) in '❌✅' and r.message.id == give_msg.id,
                    timeout=20
                ), name='sender'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: u.id == member.id and str(r.emoji) in '❌✅' and r.message.id == give_msg.id,
                    timeout=20
                ), name='receiver')
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            finished = list(done)

            for task in pending:
                try:
                    task.cancel()
                except asyncio.CancelledError:
                    pass

            action1 = finished[0].get_name()
            action2 = finished[1].get_name()
            try:
                result1 = finished[0].result()
                result2 = finished[1].result()
            except asyncio.TimeoutError:
                embed.colour = 0xfd0111
                embed.description += '**Card transfer timed out.**'
                await give_msg.edit(embed=embed)
                return

            if action1 == 'sender' and action2 == 'receiver':
                reaction_sender, sender = result1
                reaction_receiver, receiver = result2
                if str(reaction_sender.emoji) == '❌' or str(reaction_receiver.emoji) == '❌':
                    embed.colour = 0xfd0111
                    embed.description += '**Card transfer has been cancelled.**'
                    await give_msg.edit(embed=embed)
                    return
                elif str(reaction_sender.emoji) == '✅' and str(reaction_receiver.emoji) == '✅':
                    give_card(ctx.author, member, card_code)
                    embed.colour = 0x35ff42
                    embed.description += '**Card transfer completed.**'
                    await give_msg.edit(embed=embed)
                    return
                else:
                    pass
            elif action1 == 'receiver' and action2 == 'sender':
                reaction_receiver, receiver = result1
                reaction_sender, sender = result2
                if str(reaction_sender.emoji) == '❌' or str(reaction_receiver.emoji) == '❌':
                    embed.colour = 0xfd0111
                    embed.description += '**Card transfer has been cancelled.**'
                    await give_msg.edit(embed=embed)
                    return
                elif str(reaction_sender.emoji) == '✅' and str(reaction_receiver.emoji) == '✅':
                    give_card(ctx.author, member, card_code)
                    embed.colour = 0x35ff42
                    embed.description += '**Card transfer completed.**'
                    await give_msg.edit(embed=embed)
                    return
                else:
                    pass

    @commands.command(name='trade')
    async def trade(self, ctx: commands.Context, member: discord.Member, author_card_code: str, member_card_code: str):
        if not is_user_registered(ctx.author):
            await ctx.send('You should first register an account using the `start` command.')
            return
        if ctx.guild.get_member(member.id) is None:
            await ctx.send(f'User not found.')
            return
        if not is_user_registered(member):
            await ctx.send('The member you want to trade cards with is not registered. He should register an account using the `start` command.')
            return
        if ctx.author.id == member.id:
            await ctx.send(f'Sorry {ctx.author.mention}, you cannot trade cards with yourself.')
            return
        author_inventory = users.find_one({'_id': str(ctx.author.id)})['inventory']
        member_inventory = users.find_one({'_id': str(member.id)})['inventory']
        author_card_code = author_card_code.upper()
        member_card_code = member_card_code.upper()
        if author_card_code not in author_inventory:
            await ctx.send(f'{ctx.author.mention}, you do not have this card.')
            return
        if member_card_code not in member_inventory:
            await ctx.send(f'{member.mention} does not have this card.')
            return
        author_card = grabbed_cards.find_one({'_id': str(author_card_code)})
        member_card = grabbed_cards.find_one({'_id': str(member_card_code)})
        author_card_id = author_card['cardId']
        member_card_id = member_card['cardId']
        ids = [author_card_id, 'trade-arrow', member_card_id]
        imagecreation(ids).save(f'./temp_trade.png', 'PNG')
        author_card_print = author_card['print']
        member_card_print = member_card['print']
        author_generic_card = cards.find_one({'_id': str(author_card_id)})
        member_generic_card = cards.find_one({'_id': str(member_card_id)})
        author_card_wishlists = author_generic_card['wishlists']
        member_card_wishlists = member_generic_card['wishlists']
        author_card_set = author_generic_card['set']
        member_card_set = member_generic_card['set']
        author_card_name = author_generic_card['name']
        member_card_name = member_generic_card['name']
        author_card_rarity = author_generic_card['rarity']
        member_card_rarity = member_generic_card['rarity']
        with open(f'./temp_trade.png', 'rb') as f:
            embed = discord.Embed(
                title='Card trade',
                description=f'{ctx.author.mention}\n'
                            f'`{author_card_code}` · `#{author_card_print}` · `♡{str(author_card_wishlists)}` · `☆ {str(author_card_rarity)}`  · {author_card_set} · **{author_card_name}**\n\n'
                            f'{member.mention}\n'
                            f'`{member_card_code}` · `#{member_card_print}` · `♡{str(member_card_wishlists)}` · `☆ {str(member_card_rarity)}`  · {member_card_set} · **{member_card_name}**\n\n',
                colour=0xffcb05
            )
            file = discord.File(f, filename='image.png')
            embed.set_image(url=f'attachment://image.png')
            trade = await ctx.send(file=file, embed=embed)
        await trade.add_reaction('❌')
        await trade.add_reaction('✅')
        while True:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: u.id == ctx.author.id and str(r.emoji) in '❌✅' and r.message.id == trade.id,
                    timeout=20
                ), name='author'),
                asyncio.create_task(self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: u.id == member.id and str(r.emoji) in '❌✅' and r.message.id == trade.id,
                    timeout=20
                ), name='member')
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            finished = list(done)

            for task in pending:
                try:
                    task.cancel()
                except asyncio.CancelledError:
                    pass

            action1 = finished[0].get_name()
            action2 = finished[1].get_name()
            try:
                result1 = finished[0].result()
                result2 = finished[1].result()
            except asyncio.TimeoutError:
                embed.colour = 0xfd0111
                embed.description += '**Card trade timed out.**'
                await trade.edit(embed=embed)
                return

            if action1 == 'author' and action2 == 'member':
                reaction_author, author = result1
                reaction_member, member = result2
                if str(reaction_author.emoji) == '❌' or str(reaction_member.emoji) == '❌':
                    embed.colour = 0xfd0111
                    embed.description += '**Card trade has been cancelled.**'
                    await trade.edit(embed=embed)
                    return
                elif str(reaction_author.emoji) == '✅' and str(reaction_member.emoji) == '✅':
                    trade_card(ctx.author, member, author_card_code, member_card_code)
                    embed.colour = 0x35ff42
                    embed.description += '**Card trade completed.**'
                    await trade.edit(embed=embed)
                    return
                else:
                    pass
            elif action1 == 'member' and action2 == 'author':
                reaction_member, member = result1
                reaction_author, author = result2
                if str(reaction_author.emoji) == '❌' or str(reaction_member.emoji) == '❌':
                    embed.colour = 0xfd0111
                    embed.description += '**Card trade has been cancelled.**'
                    await trade.edit(embed=embed)
                    return
                elif str(reaction_author.emoji) == '✅' and str(reaction_member.emoji) == '✅':
                    trade_card(ctx.author, member, author_card_code, member_card_code)
                    embed.colour = 0x35ff42
                    embed.description += '**Card trade completed.**'
                    await trade.edit(embed=embed)
                    return
                else:
                    pass

    @trade.error
    async def trade_error(self, ctx: commands.Context, error):
        await ctx.send('Something went wrong. Please use the `help` command to check the usage of commands. ')


def setup(bot: commands.Bot):
    bot.add_cog(Trades(bot))
