from datetime import datetime, timedelta

import os
import pokebase as pb
from dotenv import load_dotenv
from pokemontcgsdk import Card
from pymongo import MongoClient

from utils import *

load_dotenv()
PSW_MONGODB = os.getenv('PSW_MONGODB')
API_KEY = os.getenv('API_KEY')

client = MongoClient(f'mongodb+srv://nick:{PSW_MONGODB}@primocluster.kqoqp.mongodb.net/discord-bot?retryWrites=true&w'
                     f'=majority')

db = client['discord-bot']

pokemons = db['pokemons']
cards = db['cards']
grabbed_cards = db['grabbed_cards']
general_bot_settings = db['general_bot_settings']
users = db['users']
guilds = db['guilds']

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

RARITY_ORDER = {
    'Common': 0,
    'Uncommon': 1,
    'Rare': 2,
    'Ultra Rare': 3,
    'Secret Rare': 4
}

RARITY_ORDER_REV = {
    0: 'Common',
    1: 'Uncommon',
    2: 'Rare',
    3: 'Ultra Rare',
    4: 'Secret Rare'
}

CLASS_RARITIES = {
    'Common': ['Common'],
    'Uncommon': ['Uncommon'],
    'Rare': ['Rare', 'Rare Shiny', 'Classic Collection', 'Rare Holo', 'Promo', 'Amazing Rare', None],
    'Ultra Rare': ['Rare Holo Prism Star', 'Rare Holo EX', 'Rare Holo LV.X', 'Rare Holo Star', 'LEGEND', 'Rare Prime', 'Rare Holo GX', 'Rare Holo V', 'Rare Holo VMAX', 'Rare Holo VSTAR', 'Rare Ultra', 'Rare BREAK', 'Rare ACE'],
    'Secret Rare': ['Rare Secret', 'Rare Shining', 'Rare Rainbow', 'Rare Shiny GX']
}

EXP_AMOUNT = {
    0: 0,
    1: 84,
    2: 178,
    3: 278,
    4: 386,
    5: 508,
    6: 642,
    7: 794,
    8: 964,
    9: 1150,
    10: 1348,
    11: 1544,
    12: 1730,
    13: 1900,
    14: 2052,
    15: 2188,
    16: 2308,
    17: 2416,
    18: 2516,
    19: 2610,
    20: 2696
}

RATES = {
    0: ['Common cards: 99%\nUncommon cards: 0.9%\nRare cards: 0.1%\nUltra rare cards: 0%\nSecret rare cards: 0%', 'Common: 99%, Uncommon: 0.9%, Rare: 0.1%, Ultra rare: 0%, Secret rare: 0%'],
    1: ['Common cards: 90%\nUncommon cards: 9%\nRare cards: 0.9%\nUltra rare cards: 0.1%\nSecret rare cards: 0%', 'Common: 90%, Uncommon: 9%, Rare: 0.9%, Ultra rare: 0.1%, Secret rare: 0%'],
    2: ['Common cards: 85%\nUncommon cards: 14%\nRare cards: 0.9%\nUltra rare cards: 0.1%\nSecret rare cards: 0%', 'Common: 85%, Uncommon: 14%, Rare: 0.9%, Ultra rare: 0.1%, Secret rare: 0%'],
    3: ['Common cards: 75%\nUncommon cards: 20%\nRare cards: 4.8%\nUltra rare cards: 0.2%\nSecret rare cards: 0%', 'Common: 75%, Uncommon: 20%, Rare: 4.8%, Ultra rare: 0.2%, Secret rare: 0%'],
    4: ['Common cards: 65%\nUncommon cards: 26%\nRare cards: 8.6%\nUltra rare cards: 0.4%\nSecret rare cards: 0%', 'Common: 65%, Uncommon: 26%, Rare: 8.6%, Ultra rare: 0.4%, Secret rare: 0%'],
    5: ['Common cards: 60%\nUncommon cards: 30%\nRare cards: 9.5%\nUltra rare cards: 0.5%\nSecret rare cards: 0%', 'Common: 60%, Uncommon: 30%, Rare: 9.5%, Ultra rare: 0.5%, Secret rare: 0%'],
    6: ['Common cards: 50%\nUncommon cards: 33%\nRare cards: 16.25%\nUltra rare cards: 0.75%\nSecret rare cards: 0%', 'Common: 50%, Uncommon: 33%, Rare: 16.25%, Ultra rare: 0.75%, Secret rare: 0%'],
    7: ['Common cards: 45%\nUncommon cards: 35%\nRare cards: 19%\nUltra rare cards: 1%\nSecret rare cards: 0%', 'Common: 45%, Uncommon: 35%, Rare: 19%, Ultra rare: 1%, Secret rare: 0%'],
    8: ['Common cards: 40%\nUncommon cards: 36%\nRare cards: 22%\nUltra rare cards: 1.99%\nSecret rare cards: 0.01%', 'Common: 40%, Uncommon: 36%, Rare: 22%, Ultra rare: 1.99%, Secret rare: 0.01%'],
    9: ['Common cards: 32%\nUncommon cards: 40%\nRare cards: 24%\nUltra rare cards: 3.95%\nSecret rare cards: 0.05%', 'Common: 32%, Uncommon: 40%, Rare: 24%, Ultra rare: 3.95%, Secret rare: 0.05%'],
    10: ['Common cards: 30%\nUncommon cards: 40%\nRare cards: 25%\nUltra rare cards: 4.9%\nSecret rare cards: 0.1%', 'Common: 30%, Uncommon: 40%, Rare: 25%, Ultra rare: 4.9%, Secret rare: 0.1%'],
    11: ['Common cards: 25%\nUncommon cards: 40%\nRare cards: 27%\nUltra rare cards: 7.75%\nSecret rare cards: 0.25%', 'Common: 25%, Uncommon: 40%, Rare: 27%, Ultra rare: 7.75%, Secret rare: 0.25%'],
    12: ['Common cards: 20%\nUncommon cards: 40%\nRare cards: 30%\nUltra rare cards: 9.5%\nSecret rare cards: 0.5%', 'Common: 20%, Uncommon: 40%, Rare: 30%, Ultra rare: 9.5%, Secret rare: 0.5%'],
    13: ['Common cards: 15%\nUncommon cards: 35%\nRare cards: 35%\nUltra rare cards: 14.25%\nSecret rare cards: 0.75%', 'Common: 15%, Uncommon: 35%, Rare: 35%, Ultra rare: 14.25%, Secret rare: 0.75%'],
    14: ['Common cards: 10%\nUncommon cards: 25%\nRare cards: 45%\nUltra rare cards: 19%\nSecret rare cards: 1%', 'Common: 10%, Uncommon: 25%, Rare: 45%, Ultra rare: 19%, Secret rare: 1%'],
    15: ['Common cards: 5%\nUncommon cards: 20%\nRare cards: 50%\nUltra rare cards: 22.5%\nSecret rare cards: 2.5%', 'Common: 5%, Uncommon: 20%, Rare: 50%, Ultra rare: 22.5%, Secret rare: 2.5%'],
    16: ['Common cards: 4%\nUncommon cards: 15%\nRare cards: 46%\nUltra rare cards: 30%\nSecret rare cards: 5%', 'Common: 4%, Uncommon: 15%, Rare: 46%, Ultra rare: 30%, Secret rare: 5%'],
    17: ['Common cards: 3%\nUncommon cards: 10%\nRare cards: 42%\nUltra rare cards: 37.5%\nSecret rare cards: 7.5%', 'Common: 3%, Uncommon: 10%, Rare: 42%, Ultra rare: 37.5%, Secret rare: 7.5%'],
    18: ['Common cards: 2%\nUncommon cards: 8%\nRare cards: 35%\nUltra rare cards: 45%\nSecret rare cards: 10%', 'Common: 2%, Uncommon: 8%, Rare: 35%, Ultra rare: 45%, Secret rare: 10%'],
    19: ['Common cards: 1%\nUncommon cards: 5%\nRare cards: 29%\nUltra rare cards: 52.5%\nSecret rare cards: 12.5%', 'Common: 1%, Uncommon: 5%, Rare: 29%, Ultra rare: 52.5%, Secret rare: 12.5%'],
    20: ['Common cards: 1%\nUncommon cards: 2%\nRare cards: 25%\nUltra rare cards: 57%\nSecret rare cards: 15%', 'Common: 1%, Uncommon: 2%, Rare: 25%, Ultra rare: 57%, Secret rare: 15%']
}


async def add_exp(ctx: commands.Context, amount):
    users.update_one({
        '_id': str(ctx.author.id)
    }, {
        '$inc': {'exp': amount}
    })
    user = users.find_one({'_id': str(ctx.author.id)})
    while user['exp'] >= EXP_AMOUNT[user['level'] + 1]:
        await level_up(ctx)


async def level_up(ctx: commands.Context):
    users.update_one({
        '_id': str(ctx.author.id)
    }, {
        '$inc': {'level': 1}
    })
    user = users.find_one({'_id': str(ctx.author.id)})
    await ctx.send(f'{ctx.author.mention}, you are now level `{user["level"]}`! Check your level and other informations with the `level` command.')


def add_pokemons(first, last):
    for i in range(first, last + 1):
        pokemon = pb.pokemon(i)
        pokemons.insert_one({
            '_id': pokemon.id,
            'name': pokemon.name,
            'sprite': pokemon.sprites.front_default,
            'sprite_shiny': pokemon.sprites.front_shiny,
            'artwork': pb.SpriteResource('pokemon/other/official-artwork', pokemon.id).url
        })


def import_all_cards():
    all_cards = Card.all()
    for i in range(len(all_cards)):
        card = all_cards[i]
        card_id = card.id
        card_name = card.name
        card_supertype = card.supertype
        card_subtypes = card.subtypes
        card_types = card.types
        card_set = card.set.name
        card_set_logo = card.set.images.logo
        card_artist = card.artist
        card_rarity = card.rarity
        card_image_lr = card.images.small
        card_image_hr = card.images.large
        cards.insert_one({
            '_id': card_id,
            'name': card_name,
            'class': card_supertype,
            'subtypes': card_subtypes,
            'types': card_types or 'None',
            'set': card_set,
            'setLogo': card_set_logo,
            'artist': card_artist,
            'rarity': card_rarity,
            'imageLow': card_image_lr,
            'imageHigh': card_image_hr
        })


def download_images():
    mongocards = list(cards.find())
    print(len(mongocards))
    for i in range(4530, 14679):
        if not os.path.exists('./imagesLow'):
            os.makedirs('./imagesLow')
        if not os.path.exists('./imagesHigh'):
            os.makedirs('./imagesHigh')
        url_low = mongocards[i]['imageLow']
        r_low = requests.get(url_low)
        filename_low = f'{url_low.split("/")[-2]}_{url_low.split("/")[-1]}'
        url_high = mongocards[i]['imageHigh']
        r_high = requests.get(url_high)
        filename_high = f'{url_high.split("/")[-2]}_{url_high.split("/")[-1]}'
        with open(f'./imagesLow/{filename_low}', 'wb') as outfile:
            outfile.write(r_low.content)
        with open(f'./imagesHigh/{filename_high}', 'wb') as outfile:
            outfile.write(r_high.content)


def get_new_card_code():
    card_code = int(general_bot_settings.find_one({
        '_id': 0
    })['lastCardCode']) + 1
    general_bot_settings.update_one({
        '_id': 0
    }, {
        '$set': {
            'lastCardCode': str(card_code)
        }
    }, upsert=False)
    return base31encode(card_code)


def get_new_temp_image_number():
    temp_image_number = int(general_bot_settings.find_one({
        '_id': 0
    })['tempImageCounter'])
    if temp_image_number >= 10:
        general_bot_settings.update_one({
            '_id': 0
        }, {
            '$set': {
                'tempImageCounter': '0'
            }
        }, upsert=False)
    else:
        general_bot_settings.update_one({
            '_id': 0
        }, {
            '$set': {
                'tempImageCounter': str(temp_image_number + 1)
            }
        }, upsert=False)
    return temp_image_number


def add_grabbed_card(ctx: commands.Context, user: discord.User, card):
    # TODO fai un array nel database generale dove metti i codici delle carte bruciate e qui fai prima il check se c'è qualche codice in quell'array
    card_code = get_new_card_code()
    spawns = card['timesSpawned'] + 1 or 1
    grabbed_cards.insert_one({
        '_id': str(card_code),
        'cardId': str(card['_id']),
        'droppedOn': str(datetime.now().strftime('%m/%d/%Y, %H:%M:%S')),
        'droppedIn': str(ctx.guild.id),
        'droppedBy': str(ctx.author.id),
        'grabbedBy': str(user.id),
        'ownedBy': str(user.id),
        'print': str(spawns)
    })
    users.update_one({
        '_id': str(user.id)
    }, {
        '$push': {
            'inventory': str(card_code)
        }})
    users.update_one({
        '_id': str(user.id)
    }, {
        '$set': {
            'lastGrab': str(datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        }})
    users.update_one({
        '_id': str(user.id)
    }, {
        '$inc': {
            'cardsGrabbed': 1
        }})
    cards.update_one({
        '_id': str(card['_id'])
    }, {
        '$set': {
            'timesSpawned': spawns
        }
    })
    return card_code


def give_card(user1: discord.Member, user2: discord.Member, card_code: str):
    users.update_one(
        {'_id': str(user1.id)},
        {'$pull': {'inventory': str(card_code)}}
    )
    user_tags = users.find_one({'_id': str(user1.id)})['tags']
    if len(user_tags) != 0:
        for tag in user_tags:
            tagged_cards = user_tags[tag]
            if card_code in tagged_cards:
                users.update_one(
                    {'_id': str(user1.id)},
                    {'$pull': {f'tags.{tag}': str(card_code)}}
                )
    users.update_one(
        {'_id': str(user2.id)},
        {'$push': {'inventory': str(card_code)}}
    )
    grabbed_cards.update_one(
        {'_id': str(card_code)},
        {'$set': {'ownedBy': str(user2.id)}}
    )
    users.update_one({'_id': str(user1.id)}, {'$inc': {'cardsGiven': 1}})
    users.update_one({'_id': str(user2.id)}, {'$inc': {'cardsReceived': 1}})


def trade_card(author: discord.Member, member: discord.Member, author_card_code: str, member_card_code: str):
    users.update_one(
        {'_id': str(author.id)},
        {'$pull': {'inventory': str(author_card_code)}}
    )
    user1_tags = users.find_one({'_id': str(author.id)})['tags']
    if len(user1_tags) != 0:
        for tag in user1_tags:
            tagged_cards = user1_tags[tag]
            if author_card_code in tagged_cards:
                users.update_one(
                    {'_id': str(author.id)},
                    {'$pull': {f'tags.{tag}': str(author_card_code)}}
                )
    users.update_one(
        {'_id': str(member.id)},
        {'$pull': {'inventory': str(member_card_code)}}
    )
    user2_tags = users.find_one({'_id': str(member.id)})['tags']
    if len(user2_tags) != 0:
        for tag in user2_tags:
            tagged_cards = user2_tags[tag]
            if member_card_code in tagged_cards:
                users.update_one(
                    {'_id': str(member.id)},
                    {'$pull': {f'tags.{tag}': str(member_card_code)}}
                )
    users.update_one(
        {'_id': str(author.id)},
        {'$push': {'inventory': str(member_card_code)}}
    )
    users.update_one(
        {'_id': str(member.id)},
        {'$push': {'inventory': str(author_card_code)}}
    )
    grabbed_cards.update_one(
        {'_id': str(author_card_code)},
        {'$set': {'ownedBy': str(member.id)}}
    )
    grabbed_cards.update_one(
        {'_id': str(member_card_code)},
        {'$set': {'ownedBy': str(author.id)}}
    )
    users.update_one({'_id': str(author.id)}, {'$inc': {'cardsGiven': 1}})
    users.update_one({'_id': str(member.id)}, {'$inc': {'cardsReceived': 1}})
    users.update_one({'_id': str(member.id)}, {'$inc': {'cardsGiven': 1}})
    users.update_one({'_id': str(author.id)}, {'$inc': {'cardsReceived': 1}})


def is_grab_cooldown(member: discord.Member):
    last_grab_str = list(users.find({'_id': str(member.id)}))[0]['lastGrab']
    last_grab_obj = datetime.strptime(last_grab_str, '%m/%d/%Y, %H:%M:%S')
    grab_end = last_grab_obj + timedelta(minutes=10, seconds=5)
    now = datetime.now()
    if now <= grab_end:
        seconds_diff = (grab_end - now).seconds
        if seconds_diff >= 60:
            minutes = seconds_diff // 60
            time_str = f'{minutes} minutes'
        else:
            time_str = f'{seconds_diff} seconds'
        return True, time_str
    else:
        return False, 0
    pass


def is_user_registered(member: discord.Member):
    if len(list(users.find({'_id': str(member.id)}))) == 0:
        return False
    else:
        return True


def sort_list_cards(owner_id: int, cards_list: list, sort_type: str = None, reverse=False) -> list:
    cards_dict_list = []
    user = users.find_one({'_id': str(owner_id)})
    for card_code in cards_list:
        card_info = grabbed_cards.find_one({'_id': str(card_code)})
        card_id = card_info['cardId']
        generic_card = cards.find_one({'_id': str(card_id)})
        card_emoji = '◾'
        for tag in user['tags']:
            if card_code in user['tags'][tag]:
                card_emoji = user['tagEmojis'][tag]
                break
        card_dict = {
            'code': str(card_code),
            'id': str(card_id),
            'name': str(generic_card['name']),
            'set': str(generic_card['set']),
            'print': int(card_info['print']),
            'rarity': str(generic_card['rarity']),
            'wishlists': int(generic_card['wishlists']),
            'emoji': str(card_emoji)
        }
        cards_dict_list.append(card_dict)
    if sort_type == 'wishlist' or sort_type == 'wl':
        return sorted(cards_dict_list, key=lambda d: d['wishlists'], reverse=not reverse)
    elif sort_type == 'print' or sort_type == 'p':
        return sorted(cards_dict_list, key=lambda d: d['print'], reverse=reverse)
    elif sort_type == 'name' or sort_type == 'n':
        return sorted(cards_dict_list, key=lambda d: d['name'], reverse=reverse)
    elif sort_type == 'set' or sort_type == 's':
        return sorted(cards_dict_list, key=lambda d: d['set'], reverse=reverse)
    elif sort_type == 'code' or sort_type == 'c':
        return sorted(cards_dict_list, key=lambda d: d['code'], reverse=reverse)
    elif sort_type == 'rarity':
        return sorted(cards_dict_list, key=lambda d: RARITY_ORDER[RARITIES[d['rarity']]], reverse=not reverse)
    elif sort_type == 'date' or sort_type == 'd':
        if reverse:
            cards_dict_list.reverse()
            return cards_dict_list
        else:
            return cards_dict_list
    else:
        return cards_dict_list


def filter_cards(owner_id: int, cards_list: list, filter_type: str, filter_query: str) -> list:
    cards_dict_list = []
    user = users.find_one({'_id': str(owner_id)})
    if filter_type == 'name' or filter_type == 'n':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_name = str(generic_card['name'])
            if bool(re.match(fr'.*{filter_query}.*', card_name, flags=re.IGNORECASE)):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': card_name,
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'set' or filter_type == 's':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_set = str(generic_card['set'])
            if bool(re.match(fr'.*{filter_query}.*', card_set, flags=re.IGNORECASE)):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': card_set,
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'print':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_print = int(card_info['print'])
            if card_print == int(filter_query):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': card_print,
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'rarity':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_rarity = str(generic_card['rarity'])
            if bool(re.match(fr'.*{filter_query}.*', card_rarity, flags=re.IGNORECASE)):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': card_rarity,
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'wishlist' or filter_type == 'wl':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_wishlists = int(generic_card['wishlists'])
            if card_wishlists == int(filter_query):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': card_wishlists,
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'spawner':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_spawner = int(card_info['droppedBy'])
            if card_spawner == int(filter_query):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'grabber':
        for card_code in cards_list:
            card_info = grabbed_cards.find_one({'_id': str(card_code)})
            card_id = card_info['cardId']
            generic_card = cards.find_one({'_id': str(card_id)})
            card_grabber = int(card_info['grabbedBy'])
            if card_grabber == int(filter_query):
                card_emoji = '◾'
                for tag in user['tags']:
                    if card_code in user['tags'][tag]:
                        card_emoji = user['tagEmojis'][tag]
                        break
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'tag' or filter_type == 't':
        try:
            for card_code in user['tags'][filter_query]:
                card_info = grabbed_cards.find_one({'_id': str(card_code)})
                card_id = card_info['cardId']
                generic_card = cards.find_one({'_id': str(card_id)})
                card_emoji = user['tagEmojis'][filter_query]
                card_dict = {
                    'code': str(card_code),
                    'id': str(card_id),
                    'name': str(generic_card['name']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
            return cards_dict_list
        except KeyError:
            return cards_dict_list
    else:
        return cards_dict_list


def sort_filtered_dict(cards_dict_list: list, sort_type: str = None, reverse=False) -> list:
    if sort_type == 'wishlist' or sort_type == 'wl':
        return sorted(cards_dict_list, key=lambda d: d['wishlists'], reverse=not reverse)
    elif sort_type == 'print' or sort_type == 'p':
        return sorted(cards_dict_list, key=lambda d: d['print'], reverse=reverse)
    elif sort_type == 'name' or sort_type == 'n':
        return sorted(cards_dict_list, key=lambda d: d['name'], reverse=reverse)
    elif sort_type == 'set' or sort_type == 's':
        return sorted(cards_dict_list, key=lambda d: d['set'], reverse=reverse)
    elif sort_type == 'code' or sort_type == 'c':
        return sorted(cards_dict_list, key=lambda d: d['code'], reverse=reverse)
    elif sort_type == 'rarity':
        return sorted(cards_dict_list, key=lambda d: RARITY_ORDER[RARITIES[d['rarity']]], reverse=not reverse)
    elif sort_type == 'date' or sort_type == 'd':
        if reverse:
            cards_dict_list.reverse()
            return cards_dict_list
        else:
            return cards_dict_list
    else:
        return cards_dict_list


def det_rewards(card_code: str) -> list:
    grabbed_card = grabbed_cards.find_one({'_id': card_code})
    card_id = grabbed_card['cardId']
    card_print = grabbed_card['print']
    card = cards.find_one({'_id': card_id})
    rarity_class = RARITIES[card['rarity']]
    multiplier = det_multiplier(card_print)
    if rarity_class == 'Common':
        rewards = [1, int(10 * multiplier)]
    elif rarity_class == 'Uncommon':
        rewards = [2, int(15 * multiplier)]
    elif rarity_class == 'Rare':
        rewards = [4, int(20 * multiplier)]
    elif rarity_class == 'Ultra Rare':
        rewards = [6, int(30 * multiplier)]
    elif rarity_class == 'Secret Rare':
        rewards = [10, int(50 * multiplier)]
    return rewards


async def burn_card(ctx: commands.Context, user_burning, rewards: list, card_code: str):
    users.update_one(
        {'_id': str(ctx.author.id)},
        {'$pull': {'inventory': card_code}}
    )
    user_tags = user_burning['tags']
    if len(user_tags) != 0:
        for tag in user_tags:
            tagged_cards = user_tags[tag]
            if card_code in tagged_cards:
                users.update_one(
                    {'_id': str(ctx.author.id)},
                    {'$pull': {f'tags.{tag}': str(card_code)}}
                )
    users.update_one(
        {'_id': str(ctx.author.id)},
        {'$inc': {'coins': rewards[1]}}
    )
    users.update_one(
        {'_id': str(ctx.author.id)},
        {'$inc': {'cardsBurned': 1}}
    )
    general_bot_settings.update_one({'_id': 0},
                                    {'$push': {'freeCodes': card_code}})
    await add_exp(ctx, rewards[0])
    grabbed_cards.delete_one({'_id': card_code})
