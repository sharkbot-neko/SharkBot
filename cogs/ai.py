from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
from alphabet2kana import a2k
from openai import AsyncOpenAI
import time
from discord import app_commands
import asyncio
import re
from functools import partial
from urllib.parse import quote
import time
import json
import aiohttp

from openai import AsyncOpenAI

cooldown_summary = {}

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.aito = self.tkj["AIChat"]
        print(f"init -> AICog")

    @commands.hybrid_group(name="ai", description="このチャンネルの過去30件分の会話を要約します。", fallback="summary")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ai_automod(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        if not ctx.interaction:
            return await ctx.reply(ephemeral=True, content="スラッシュコマンドからお願いします。")

        current_time = time.time()
        last_message_time = cooldown_summary.get(ctx.guild.id, 0)
        if current_time - last_message_time < 60:
            return await ctx.reply(ephemeral=True, content="クールダウン中です。")
        cooldown_summary[ctx.guild.id] = current_time

        client = AsyncOpenAI(
            api_key=self.aito,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        p = ""

        async for t in ctx.channel.history(limit=30):
            try:
                p += t.content[:80] + "\n"
            except:
                continue

        prompt = f"以下の文章を日本語で3個の短い箇条書きに要約してください:\n\n{p}"

        response = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return await ctx.reply(f"{response.choices[0].message.content}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AICog(bot))