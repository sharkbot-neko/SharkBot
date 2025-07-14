from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
from discord import Webhook
import aiohttp

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CharacterCog")

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))