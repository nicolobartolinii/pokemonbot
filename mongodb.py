from pymongo import MongoClient
import pokebase as pb
from dotenv import load_dotenv
import os
from pokemontcgsdk import Card
from pokemontcgsdk import Set
import requests

load_dotenv()
PSW_MONGODB = os.getenv('PSW_MONGODB')
API_KEY = os.getenv('API_KEY')

client = MongoClient(f'mongodb+srv://nick:{PSW_MONGODB}@primocluster.kqoqp.mongodb.net/discord-bot?retryWrites=true&w'
                     f'=majority')

db = client['discord-bot']

pokemons = db['pokemons']
cards = db['cards']


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


# card = Card.where(q='id:"pl1-1"')
# cards.insert_one({
#     '_id': card[0].id,
#     'types': card[0].types
# })

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


mongocards = list(cards.find())
print(len(mongocards))
print(mongocards[0])
for mongocard in mongocards:
    if not os.path.exists('./logos'):
        os.makedirs('./logos')
    if not os.path.exists('./imagesLow'):
        os.makedirs('./imagesLow')
    if not os.path.exists('./imagesHigh'):
        os.makedirs('./imagesHigh')
    url_logo = mongocard['setLogo']
    r_logo = requests.get(url_logo)
    filename_logo = f'{url_logo.split("/")[-2]}_{url_logo.split("/")[-1]}'
    url_low = mongocard['imageLow']
    r_low = requests.get(url_low)
    filename_low = f'{url_low.split("/")[-2]}_{url_low.split("/")[-1]}'
    url_high = mongocard['imageHigh']
    r_high = requests.get(url_high)
    filename_high = f'{url_high.split("/")[-2]}_{url_high.split("/")[-1]}'
    with open(f'./logos/{filename_logo}', 'wb') as outfile:
        outfile.write(r_logo.content)
    with open(f'./imagesLow/{filename_low}', 'wb') as outfile:
        outfile.write(r_low.content)
    with open(f'./imagesHigh/{filename_high}', 'wb') as outfile:
        outfile.write(r_high.content)
