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

class CreditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CreditCog")

    @commands.hybrid_group(name="credit", description="サーバー内信頼度スコアを追加します。", fallback="add")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def credit_add(self, ctx: commands.Context, メンバー: discord.Member, スコア: int):
        try:
            await ctx.defer()
            db = self.bot.async_db["Main"].GuildCredit
            user_data = await db.find_one({"_id": メンバー.id, "Guild": ctx.guild.id})
            if user_data:
                await db.update_one({"_id": メンバー.id, "Guild": ctx.guild.id}, {"$inc": {"credit": スコア}})
            else:
                await db.insert_one({"_id": メンバー.id, "credit": スコア + 100, "Guild": ctx.guild.id})
            await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを追加しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを追加できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @credit_add.command(name="remove", description="サーバー内信頼度スコアを減らします。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def credit_remove(self, ctx: commands.Context, メンバー: discord.Member, スコア: int):
        try:
            await ctx.defer()
            db = self.bot.async_db["Main"].GuildCredit
            user_data = await db.find_one({"_id": メンバー.id, "Guild": ctx.guild.id})
            if user_data:
                await db.update_one({"_id": メンバー.id, "Guild": ctx.guild.id}, {"$inc": {"credit": -スコア}})
            else:
                await db.insert_one({"_id": メンバー.id, "credit": -スコア + 100, "Guild": ctx.guild.id})
            await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを減らしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを減らせませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @credit_add.command(name="check", description="サーバー内信頼度スコアをチェックします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def credit_check(self, ctx: commands.Context, メンバー: discord.Member):
        try:
            await ctx.defer()
            db = self.bot.async_db["Main"].GuildCredit
            user_data = await db.find_one({"_id": メンバー.id, "Guild": ctx.guild.id})
            if user_data:
                await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを参照しました。", description=f"{user_data["credit"]}/100", color=discord.Color.blue()))
            else:
                return await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを参照しました。", description=f"100/100", color=discord.Color.blue()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="サーバー内信頼度スコアを参照できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

async def setup(bot):
    await bot.add_cog(CreditCog(bot))