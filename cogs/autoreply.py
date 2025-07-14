from discord.ext import commands
import discord
from discord import app_commands
import traceback
import sys
import logging
import asyncio
import re
import datetime
import time
import random

COOLDOWN_TIME = 10
user_last_message_time = {}

COOLDOWN_TIME = 5
user_last_message_time2 = {}

class AutoReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> AutoReplyCog")

    @commands.Cog.listener("on_message")
    async def on_message_ul(self, message):
        if message.author.bot:
            return
        if not message.content:
            return
        if "@" in message.content:
            return
        db = self.bot.async_db["Main"].ExpandSettingsUser
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        pattern = r"\d{17,19}"
        current_time = time.time()
        last_message_time = user_last_message_time2.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time2[message.guild.id] = current_time
        msg = [int(match) for match in re.findall(pattern, message.content)]
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            us = self.bot.get_user(msg[0])
            if us:
                if us.avatar:
                    await message.reply(embed=discord.Embed(title=f"{us.display_name}の情報", color=discord.Color.green()).set_thumbnail(url=us.avatar.url).add_field(name="基本情報", value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**"))
                else:
                    await message.reply(embed=discord.Embed(title=f"{us.display_name}の情報", color=discord.Color.green()).add_field(name="基本情報", value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**"))
        except:
            return

async def setup(bot):
    await bot.add_cog(AutoReplyCog(bot))