from discord.ext import commands
import discord
import traceback
from deep_translator import GoogleTranslator
import sys
import logging
import random
import time
import asyncio
import re
from discord import Webhook
from functools import partial
import aiohttp
import time

class ScriptCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ScriptCog")

    # 後で実装

async def setup(bot):
    await bot.add_cog(ScriptCog(bot))