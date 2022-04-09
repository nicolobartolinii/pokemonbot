import re
from io import BytesIO
import random
import discord
import requests
from PIL import Image
from discord.ext import commands

RARITIES = {
    'Common': 'Common',
    'Uncommon': 'Uncommon',
    'Rare': 'Rare',
    'Rare Shiny': 'Rare',
    'Classic Collection': 'Rare',
    'Rare Holo': 'Rare',
    'Promo': 'Rare',
    'Amazing Rare': 'Rare',
    None: 'Rare',
    'null': 'Rare',
    'None': 'Rare',
    'Rare Holo Prism Star': 'Ultra Rare',
    'Rare Holo EX': 'Ultra Rare',
    'Rare Holo LV.X': 'Ultra Rare',
    'Rare Holo Star': 'Ultra Rare',
    'LEGEND': 'Ultra Rare',
    'Rare Prime': 'Ultra Rare',
    'Rare Holo GX': 'Ultra Rare',
    'Rare Holo V': 'Ultra Rare',
    'Rare Holo VMAX': 'Ultra Rare',
    'V': 'Ultra Rare',
    'VM': 'Ultra Rare',
    'Rare Holo VSTAR': 'Ultra Rare',
    'Rare Ultra': 'Ultra Rare',
    'Rare BREAK': 'Ultra Rare',
    'Rare ACE': 'Ultra Rare',
    'Rare Secret': 'Secret Rare',
    'Rare Shining': 'Secret Rare',
    'Rare Rainbow': 'Secret Rare',
    'Rare Shiny GX': 'Secret Rare'
}

PROB_LVLS = {
    1: [900, 100, 0, 0, 0],
    2: [750, 200, 50, 0, 0],
    3: [750, 200, 50, 0, 0],
    4: [750, 200, 50, 0, 0],
    5: [750, 200, 50, 0, 0],
    6: [750, 200, 50, 0, 0],
    7: [750, 200, 50, 0, 0],
    8: [750, 200, 50, 0, 0],
    9: [750, 200, 50, 0, 0],
    10: [750, 200, 50, 0, 0],
    11: [750, 200, 50, 0, 0],
    12: [750, 200, 50, 0, 0],
    13: [750, 200, 50, 0, 0],
    14: [750, 200, 50, 0, 0],
    15: [750, 200, 50, 0, 0]
}


def create_array(lvl):
    print(f'Creating array for level {lvl}')
    array = []
    for j in range(5):
        for _ in range(PROB_LVLS[lvl][j]):
            array.append(j)
    return array


arrays = []
for i in range(1, 16):
    arrays.append(create_array(i))


PROB_RARITIES = {
    1: arrays[1 - 1],
    2: arrays[2 - 1],
    3: arrays[3 - 1],
    4: arrays[4 - 1],
    5: arrays[5 - 1],
    6: arrays[6 - 1],
    7: arrays[7 - 1],
    8: arrays[8 - 1],
    9: arrays[9 - 1],
    10: arrays[10 - 1],
    11: arrays[11 - 1],
    12: arrays[12 - 1],
    13: arrays[13 - 1],
    14: arrays[14 - 1],
    15: arrays[15 - 1]
}


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
    if ids[1] != 'trade-arrow':
        images = [f'./imagesHigh/{card_id.split("-")[0]}_{card_id.split("-")[1]}_hires.png' for card_id in ids]
        images = [Image.open(image).resize((367, 512)) for image in images]
    else:
        images = [f'./imagesHigh/{card_id.split("-")[0]}_{card_id.split("-")[1]}_hires.png' for card_id in ids]
        images[0] = Image.open(images[0]).resize((367, 512))
        images[1] = Image.open(images[1])
        images[2] = Image.open(images[2]).resize((367, 512))
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


async def create_send_embed_lookup(ctx: commands.Context, card_name: str, card_set: str, card_wishlists: int, card_print: int, card_rarity: str, card_id: str, card_artist: str):
    embed = discord.Embed(title='Card Lookup', description=f'Card name · **{str(card_name)}**\n',
                          colour=0xffcb05)
    embed.description += f'Card set · **{str(card_set)}**\n'
    embed.description += f'Wishlists · **{str(card_wishlists)}**\n'
    embed.description += f'Total printed · **{str(card_print)}**\n'
    embed.description += f'Rarity · **{str(card_rarity)} ({str(RARITIES[str(card_rarity)])})**\n'
    embed.description += f'Artist · **{str(card_artist)}**'
    card_image = f'./imagesLow/{card_id.split("-")[0]}_{card_id.split("-")[1]}.png'
    file = discord.File(card_image, filename='image.png')
    embed.set_thumbnail(url='attachment://image.png')
    await ctx.send(file=file, embed=embed)


def extrapolate_query(query: str):
    query_list = re.split(r'\s*[:=\s]\s*', query)
    try:
        index_order = query_list.index('o')
    except ValueError:
        try:
            index_order = query_list.index('order')
        except ValueError:
            index_order = None
    try:
        index_filter = query_list.index('f')
    except ValueError:
        try:
            index_filter = query_list.index('filter')
        except ValueError:
            index_filter = None
    if index_order is not None and index_filter is None:
        order_specs = query_list[index_order + 1:]
        if order_specs[-1] == 'r' or order_specs[-1] == 'reverse':
            return 0, order_specs[:-1], True
        else:
            return 0, order_specs, False
    elif index_order is None and index_filter is not None:
        filter_specs = query_list[index_filter + 1:]
        return 1, filter_specs
    elif index_order is not None and index_filter is not None:
        order_specs = query_list[index_order + 1:index_filter] if index_order < index_filter else query_list[index_order + 1:]
        filter_specs = query_list[index_filter + 1:] if index_order < index_filter else query_list[index_filter + 1:index_order]
        if order_specs[-1] == 'r' or order_specs[-1] == 'reverse':
            return 2, order_specs[:-1], True, filter_specs
        else:
            return 2, order_specs, False, filter_specs
    else:
        return 3, 'error'
