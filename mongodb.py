from pymongo import MongoClient
import pokebase as pb
from dotenv import load_dotenv
import os
from pokemontcgsdk import Card
from pokemontcgsdk import Set

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


mongocards = cards.find()
