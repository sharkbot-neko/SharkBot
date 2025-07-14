from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio

class EmojiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> EmojiCog")

async def setup(bot):
    await bot.add_cog(EmojiCog(bot))