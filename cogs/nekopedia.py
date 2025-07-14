from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio

COOLDOWN_TIME = 5
user_last_message_time = {}

class NekoPediaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> NekoPediaCog")

async def setup(bot):
    await bot.add_cog(NekoPediaCog(bot))