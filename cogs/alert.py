from discord.ext import commands, tasks
from discord import Webhook
import io
import discord
import io
import traceback
import sys
import base64
import feedparser
import aiohttp
from functools import partial
import json
import asyncio
import requests
from bs4 import BeautifulSoup

class AlertCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(AlertCog(bot))