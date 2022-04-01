import os
import random

import discord
from PIL import Image
import requests
from io import BytesIO

from discord.ext import commands


def compose_images(image_urls):
    bg_url, *other_urls = image_urls
    print(bg_url)
    print(other_urls)
    response_bg = requests.get(bg_url)
    image = Image.open(BytesIO(response_bg.content)).convert('RGBA')
    for fg_name in other_urls:
        response_fg = requests.get(fg_name)
        foreground = Image.open(BytesIO(response_fg.content)).convert('RGBA')
        image.paste(foreground, (foreground.width, 0), foreground)
    return image


def imagecreation(ids):  # function to create an image
    images = [f'./imagesHigh/{id.split("-")[0]}_{id.split("-")[1]}_hires.png' for id in ids]
    images = [Image.open(image).resize((367, 512)) for image in images]
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)+140
    max_height = max(heights)+60
    new_im = Image.new('RGBA', (total_width, max_height), (255, 0, 0, 0))
    x_offset = 50
    y_offset = 30
    for im in images:
        new_im.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]+20
    return new_im


def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36


async def create_send_embed_lookup(ctx: commands.Context, card_name: str, card_set: str, card_print: int, card_rarity: str, card_id: str):
    embed = discord.Embed(title='Card Lookup', description=f'Card name · **{str(card_name)}**\n',
                          colour=0xffcb05)
    embed.description += f'Card set · **{str(card_set)}**\n'
    embed.description += f'Total printed · **{str(card_print)}**\n'
    embed.description += f'Rarity · **{str(card_rarity)}**'
    card_image = f'./imagesLow/{card_id.split("-")[0]}_{card_id.split("-")[1]}.png'
    file = discord.File(card_image, filename='image.png')
    embed.set_thumbnail(url='attachment://image.png')
    await ctx.send(file=file, embed=embed)
