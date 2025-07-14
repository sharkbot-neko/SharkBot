from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
from discord import Webhook
import ssl
import aiohttp
import datetime
from bs4 import BeautifulSoup

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class GreetingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> GreetingCog")

    @commands.command(name="greeting", description="一日の終わりのあいさつをします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def greeting(self, ctx: commands.Context):
        dt = datetime.datetime.today()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www3.nhk.or.jp/news/', ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.find_all('h1', class_="content--header-title")[0]
                url = title.find_all('a')[0]
                await ctx.reply(content=f"""今日も一日お疲れ様でした！
今日は、{dt.strftime('%Y年%m月%d日')}です！
https://www3.nhk.or.jp{url["href"]}
                                """)

async def setup(bot):
    await bot.add_cog(GreetingCog(bot))