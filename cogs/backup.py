from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import json
import aiohttp
import asyncio
import re
from functools import partial
import time

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> BackupCog")

async def setup(bot):
    await bot.add_cog(BackupCog(bot))