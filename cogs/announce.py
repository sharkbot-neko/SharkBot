from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import re
import aiohttp
from discord import Webhook
from functools import partial
import time

cooldown_announce_pub = {}

class AnnounceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> AnnounceCog")

    async def announce_pun_set_setting(self, guild: discord.Guild, channel: discord.TextChannel, tf = False):
        db = self.bot.async_db["Main"].AnnouncePun
        if not tf:
            return await db.delete_one({"Guild": guild.id})
        else:
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id}, 
                {"Guild": guild.id, "Channel": channel.id}, 
                upsert=True
            )

    async def announce_pun_get(self, guild: discord.Guild, ch: discord.TextChannel):
        db = self.bot.async_db["Main"].AnnouncePun
        try:
            dbfind = await db.find_one({"Guild": guild.id, "Channel": ch.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            return self.bot.get_channel(dbfind["Channel"])
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.author == self.bot.user:
            return
        
        check = await self.announce_pun_get(message.guild, message.channel)
        if not check or not isinstance(check, discord.TextChannel) or check.id != message.channel.id:
            return
        
        current_time = time.time()
        last_message_time = cooldown_announce_pub.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        
        cooldown_announce_pub[message.guild.id] = current_time
        
        try:
            print(f"{message.channel.name}を公開しました。")
            await message.publish()
        except discord.Forbidden as e:
            print(f"{message.guild.id} のメッセージ公開に失敗しました: {e}")

async def setup(bot):
    await bot.add_cog(AnnounceCog(bot))