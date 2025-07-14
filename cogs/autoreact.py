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

cooldown_auto_reaction = {}

class AutoReactCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> AutoReactCog")

    @commands.Cog.listener("on_message")
    async def on_message_auto_reaction_channel(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].AutoReactionChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_auto_reaction.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_auto_reaction[message.guild.id] = current_time
        em = dbfind.get("Emoji", None)
        if not em:
            return
        if em == "random":
            try:
                r_em = random.choice(list(message.guild.emojis))
                await message.add_reaction(r_em)
            except:
                return
        try:
            await message.add_reaction(em)
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_auto_reaction_word(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].AutoReactionWord
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Word": message.content}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_auto_reaction.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_auto_reaction[message.guild.id] = current_time
        em = dbfind.get("Emoji", None)
        if not em:
            return
        if em == "random":
            try:
                r_em = random.choice(list(message.guild.emojis))
                await message.add_reaction(r_em)
            except:
                return
        try:
            await message.add_reaction(em)
        except:
            return

    @commands.hybrid_group(name="autoreact", description="自動リアクションをするチャンネルを設定します。", fallback="channel")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def autoreact_channel(self, ctx: commands.Context, 絵文字: str):
        db = self.bot.async_db["Main"].AutoReactionChannel
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Emoji": 絵文字}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="自動リアクションを設定しました。", description=f"絵文字: {絵文字}\nチャンネル: {ctx.channel.mention}", color=discord.Color.green()))

    @autoreact_channel.command(name="word", description="自動リアクションをするワードを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def autoreact_word(self, ctx: commands.Context, 言葉: str, 絵文字: str):
        db = self.bot.async_db["Main"].AutoReactionWord
        await db.replace_one(
            {"Guild": ctx.guild.id, "Word": 言葉}, 
            {"Guild": ctx.guild.id, "Word": 言葉, "Emoji": 絵文字}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="自動リアクションを設定しました。", description=f"絵文字: {絵文字}", color=discord.Color.green()))

    @autoreact_channel.command(name="remove", description="自動リアクションを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def autoreact_remove(self, ctx: commands.Context, ワード: str = None):
        db = self.bot.async_db["Main"].AutoReactionChannel
        await db.delete_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}
        )
        if ワード:
            db_word = self.bot.async_db["Main"].AutoReactionWord
            await db_word.delete_one(
                {"Guild": ctx.guild.id, "Word": ワード}
            )
        await ctx.reply(embed=discord.Embed(title="自動リアクションを削除しました。", color=discord.Color.green()))

    @autoreact_channel.command(name="list", description="自動リアクションをリスト化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def autoreact_list(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].AutoReactionWord
        word_list = [f"{b.get("Word")} - {b.get("Emoji")}" async for b in db.find({"Guild": ctx.guild.id})]
        db_channel = self.bot.async_db["Main"].AutoReactionChannel
        channel_list = [f"{ctx.guild.get_channel(b.get("Channel")).mention} - {b.get("Emoji")}" async for b in db_channel.find({"Guild": ctx.guild.id})]
        await ctx.reply(embed=discord.Embed(title="自動リアクションのリスト", color=discord.Color.green()).add_field(name="特定のワードに対して", value="\n".join(word_list)).add_field(name="チャンネルに対して", value="\n".join(channel_list)))

async def setup(bot):
    await bot.add_cog(AutoReactCog(bot))