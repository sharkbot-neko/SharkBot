from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import aiohttp
from discord import Webhook

cooldown_count = {}

class CountCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CountCog")

    async def get_counting_setting(self, message: discord.Message):
        db_settings = self.bot.async_db["Main"].CountingSettings
        try:
            dbfind = await db_settings.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return {"Reset": False}
        if dbfind is None:
            return {"Reset": False}
        if dbfind.get("Reset", "no") == "yes":
            return {"Reset": True}
        else:
            return {"Reset": False}

    @commands.Cog.listener("on_message")
    async def on_message_count(self, message: discord.Message):
        if message.author.bot:
            return
        
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        
        current_time = time.time()
        last_message_time = cooldown_count.get(message.guild.id, 0)
        if current_time - last_message_time < 1:
            return
        cooldown_count[message.guild.id] = current_time

        try:

            if dbfind.get("Now", 0) + 1 != int(message.content):
                reset = await self.get_counting_setting(message)
                if reset.get("Reset") == False:
                    await message.reply(embed=discord.Embed(title="カウントに失敗しました・・", description="1から数えなおそう！", color=discord.Color.red()))
                    await db.replace_one(
                        {"Guild": message.guild.id, "Channel": message.channel.id}, 
                        {"Guild": message.guild.id, "Channel": message.channel.id, "Now": 0}, 
                        upsert=True
                    )
                    return
                else:
                    await message.reply(embed=discord.Embed(title="カウントに失敗しました・・", description="気にしないで！\n続きから数えよう！", color=discord.Color.red()))
                    return

            await db.update_one(
                {"Channel": message.channel.id},
                {"$inc": {"Now": 1}},
                upsert=True
            )

            await message.add_reaction("✅")
        except:
            return

    @commands.hybrid_group(name="count", description="カウントゲームをします。", fallback="setup")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def count_setup(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        db = self.bot.async_db["Main"].Counting
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Now": 0}, 
            upsert=True
        )
        await ctx.channel.send(embed=discord.Embed(title="カウントをセットアップしました。", description="1から数えてみよう！", color=discord.Color.green()))
        await ctx.reply(embed=discord.Embed(title="カウントをセットアップしました。", color=discord.Color.green()))

    @count_setup.command(name="disable", description="カウントゲームを終了します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def count_disable(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        db = self.bot.async_db["Main"].Counting
        result = await db.delete_one({"Channel": ctx.channel.id})
        if result.deleted_count == 0:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        return await ctx.reply(embed=discord.Embed(title="カウントを無効化しました。", color=discord.Color.red()))
    
    @count_setup.command(name="skip", description="カウントゲームの現在の数字を設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def count_skip(self, ctx: commands.Context, 数字: int):
        await ctx.defer()
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Now": 数字}, 
            upsert=True
        )
        return await ctx.reply(embed=discord.Embed(title="カウントゲームの現在の数字を変更しました。", description=f"次は{数字+1}からカウントしましょう！", color=discord.Color.green()))

    @count_setup.command(name="reset", description="カウントゲームをリセットします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def count_reset(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Now": 0}, 
            upsert=True
        )
        return await ctx.reply(embed=discord.Embed(title="カウントゲームの現在の数字をリセットしました。", description=f"次は1からカウントしましょう！", color=discord.Color.green()))

    @count_setup.command(name="settings", description="カウントゲームの詳細設定をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def count_settings(self, ctx: commands.Context, 間違えたときにリセットしないか: bool):
        await ctx.defer()
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="このチャンネルではカウントは有効ではありません。", color=discord.Color.red()))
        db_settings = self.bot.async_db["Main"].CountingSettings
        await db_settings.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Reset": "yes" if 間違えたときにリセットしないか else "no"}, 
            upsert=True
        )
        return await ctx.reply(embed=discord.Embed(title="カウントゲームの詳細設定をしました。", description=f"""
間違えたときにリセットしないか: `{"はい" if 間違えたときにリセットしないか else "いいえ"}`
""", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(CountCog(bot))