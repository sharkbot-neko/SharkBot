import discord
from discord.ext import commands
import time
import requests
from bs4 import BeautifulSoup
from functools import partial
import asyncio
from urusaiyatu import urusaiyatu
import re

class UrusaiyatuCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="market")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def market_fetch(self, ctx: commands.Context):
        item = urusaiyatu.Item()
        Market = await urusaiyatu.Market().fetch()
        desc = ""
        for m in Market:
            item_ = await item.fetch(m["it"])
            desc += f"{item_["name"]}x{m["cn"]}\n"
        await ctx.reply(embed=discord.Embed(title="うるさいやつのマーケット", description=desc, color=discord.Color.blue()))

async def setup(bot):
    await bot.add_cog(UrusaiyatuCog(bot))