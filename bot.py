import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='p$', intents=intents)
bot.load_extension('spawning')
bot.load_extension('events')

bot.run(TOKEN)
