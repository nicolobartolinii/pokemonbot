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
    0: [990, 9, 1, 0, 0],
    1: [900, 90, 9, 1, 0],
    2: [850, 140, 9, 1, 0],
    3: [750, 200, 48, 2, 0],
    4: [650, 260, 86, 4, 0],
    5: [600, 300, 95, 5, 0],
    6: [5000, 3300, 1625, 75, 0],
    7: [450, 350, 190, 10, 0],
    8: [4000, 3600, 2200, 199, 1],
    9: [3200, 4000, 2400, 395, 5],
    10: [300, 400, 250, 49, 1],
    11: [2500, 4000, 2700, 775, 25],
    12: [200, 400, 300, 95, 5],
    13: [1500, 3500, 3500, 1425, 75],
    14: [100, 250, 450, 190, 10],
    15: [50, 200, 500, 225, 25],
    16: [40, 150, 460, 300, 50],
    17: [30, 100, 420, 375, 75],
    18: [20, 200, 350, 450, 100],
    19: [10, 200, 290, 525, 125],
    20: [10, 200, 250, 570, 150],
}


def create_array(lvl):
    print(f'Creating array for level {lvl}')
    array = []
    for j in range(5):
        for _ in range(PROB_LVLS[lvl][j]):
            array.append(j)
    return array


arrays = []
for i in range(21):
    arrays.append(create_array(i))


PROB_RARITIES = {
    0: arrays[0],
    1: arrays[1],
    2: arrays[2],
    3: arrays[3],
    4: arrays[4],
    5: arrays[5],
    6: arrays[6],
    7: arrays[7],
    8: arrays[8],
    9: arrays[9],
    10: arrays[10],
    11: arrays[11],
    12: arrays[12],
    13: arrays[13],
    14: arrays[14],
    15: arrays[15],
    16: arrays[16],
    17: arrays[17],
    18: arrays[18],
    19: arrays[19],
    20: arrays[20]
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


def base31encode(number, alphabet='0123456789BCDFGHJKLMNPQRSTVWXYZ'):
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
