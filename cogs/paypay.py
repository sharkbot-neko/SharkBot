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
from PayPaython_mobile import PayPay
import time

class PayPay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> PayPay")



async def setup(bot):
    await bot.add_cog(PayPay(bot))