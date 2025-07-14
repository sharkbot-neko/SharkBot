from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
from discord import app_commands
import asyncio
import re
from functools import partial
import time
import json

class HostingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> HostingCog")

async def setup(bot):
    await bot.add_cog(HostingCog(bot))