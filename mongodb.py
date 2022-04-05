from datetime import datetime, timedelta

import discord
from discord.ext import commands
from pymongo import MongoClient
import pokebase as pb
from dotenv import load_dotenv
from pokemontcgsdk import Card
import os
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
    return base36encode(card_code)


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
        'droppedBy': str(ctx.author.id) or 'Server',
        'grabbedBy': str(user.id),
        'ownedBy': str(user.id),
        'print': str(spawns)
        # TODO server in cui è stata droppata la carta
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
    users.update_one(
        {'_id': str(member.id)},
        {'$pull': {'inventory': str(member_card_code)}}
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
        time_str = ''
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
    elif sort_type == 'print':
        return sorted(cards_dict_list, key=lambda d: d['print'], reverse=reverse)
    elif sort_type == 'name' or sort_type == 'n':
        return sorted(cards_dict_list, key=lambda d: d['name'], reverse=reverse)
    elif sort_type == 'set' or sort_type == 's':
        return sorted(cards_dict_list, key=lambda d: d['set'], reverse=reverse)
    elif sort_type == 'code' or sort_type == 'c':
        return sorted(cards_dict_list, key=lambda d: d['code'], reverse=reverse)
    elif sort_type == 'rarity':
        pass
    elif sort_type == 'date':
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
                    'name': str(generic_card['set']),
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
                    'name': str(generic_card['set']),
                    'set': str(generic_card['set']),
                    'print': card_print,
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    elif filter_type == 'rarity' or filter_type == 'r':
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
                    'name': str(generic_card['set']),
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
                    'name': str(generic_card['set']),
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
                    'name': str(generic_card['set']),
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
                    'name': str(generic_card['set']),
                    'set': str(generic_card['set']),
                    'print': int(card_info['print']),
                    'rarity': str(generic_card['rarity']),
                    'wishlists': int(generic_card['wishlists']),
                    'emoji': str(card_emoji)
                }
                cards_dict_list.append(card_dict)
        return cards_dict_list
    else:
        return cards_dict_list
