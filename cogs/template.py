from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import re
from functools import partial
import time

class TemplateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> TemplateCog")

async def setup(bot):
    await bot.add_cog(TemplateCog(bot))