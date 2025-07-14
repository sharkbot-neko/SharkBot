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

class SupportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> SupportCog")

    @commands.command(name="obj_panel")
    @commands.is_owner()
    async def obj_panel(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="サーバーに異議申し立てをする", color=discord.Color.blue(), description="以下のボタンから異議申し立てができます。"), view=discord.ui.View().add_item(discord.ui.Button(label="異議申し立て", custom_id="obj+")))
        return

async def setup(bot):
    await bot.add_cog(SupportCog(bot))