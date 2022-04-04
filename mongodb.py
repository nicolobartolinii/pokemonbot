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
