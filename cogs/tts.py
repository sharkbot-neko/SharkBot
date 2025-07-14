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

class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> TTSCog")

    @commands.hybrid_group(name="tts", description="読み上げをします。", fallback="start")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tts_start(self, ctx: commands.Context):
        if not ctx.author.voice:
            return await ctx.reply(embed=discord.Embed(title="読み上げ接続に失敗しました。", color=discord.Color.red()), ephemeral=True)
        try:
            await ctx.author.voice.channel.connect()
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title="エラーが発生しました。", description=f"```{e}```", color=discord.Color.red()))
            return
        ttscheck = self.bot.async_db["Main"].TTSCheckBeta
        await ttscheck.replace_one(
            {"Guild": ctx.guild.id},
            {"Channel": ctx.channel.id, "Guild": ctx.guild.id},
            upsert=True
        )
        print("BotがVCに参加しました！")
        return await ctx.reply(embed=discord.Embed(title="接続しました。", description="この機能はベータ版です。\n不具合があったらサポートサーバーに来てください。", color=discord.Color.green()))

    @tts_start.command(name="end", description="読み上げを終了します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tts_end(self, ctx: commands.Context):
        await ctx.voice_client.disconnect()
        ttscheck = self.bot.async_db["Main"].TTSCheckBeta
        await ttscheck.delete_one(
            {"Guild": ctx.guild.id}
        )
        print("BotがVCから退出しました！")
        return await ctx.reply(embed=discord.Embed(title="退出しました。", color=discord.Color.green()))
    
    async def tts_guilds(self):
        db = self.bot.async_db["Main"].TTSCheckBeta
        return await db.count_documents({})

    @tts_start.command(name="info", description="読み上げしているサーバー数を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tts_info(self, ctx: commands.Context):
        g_c = await self.tts_guilds()
        if g_c < 3:
            return await ctx.reply(embed=discord.Embed(title="読み上げを使用しているサーバー数", description=f"{g_c}サーバー\n読み上げは快適だと思います。", color=discord.Color.blue()))
        return await ctx.reply(embed=discord.Embed(title="読み上げを使用しているサーバー数", description=f"{g_c}サーバー\n読み上げは重いかもしれないです。", color=discord.Color.blue()))
    
    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_tts(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id == self.bot.user.id:
            if before.channel and not after.channel:
                ttscheck = self.bot.async_db["Main"].TTSCheckBeta
                await ttscheck.delete_one(
                    {"Guild": member.guild.id}
                )
                print("BotがVCからキックされました！")
            return

    @commands.Cog.listener(name="on_message")
    async def on_message_tts(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if not message.content:
            return
        if not message.author.voice:
            return
        if not message.guild.voice_client:
            return
        try:
            ttscheck = self.bot.async_db["Main"].TTSCheckBeta
            try:
                ttscheckfind = await ttscheck.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                return
            if ttscheckfind is None:
                return
            if "http" in message.content:
                return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=URL"))
            if "@" in message.content:
                return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=メンション"))
            if "#" in message.content:
                return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=チャンネル"))
            if len(message.content) > 50:
                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=省略しました。"))
                return
            message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji={message.content}"))
        except Exception as e:
            await message.channel.send(embed=discord.Embed(title="エラーが発生しました。", description=f"```{e}```", color=discord.Color.red()))
            ttscheck = self.bot.async_db["Main"].TTSCheckBeta
            await ttscheck.delete_one(
                {"Guild": message.guild.id}
            )
            return await message.guild.voice_client.disconnect()

async def setup(bot):
    await bot.add_cog(TTSCog(bot))