from discord.ext import commands, tasks
from discord import Webhook
import io
import discord
import io
import traceback
import sys
import base64
import feedparser
import aiohttp
from functools import partial
import json
import asyncio
import random
import requests
from bs4 import BeautifulSoup
import datetime

cooldown_eventalert = {}

class TimeSignalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages = {
            (0, 0): "0時です。おやすみなさい。",
            (1, 0): "1時です。まだ寝てるかな？",
            (2, 0): "2時です。まだ寝てるよね？",
            (3, 0): "3時です。まだ寝てるはずだよ？",
            (4, 0): "4時です。そろそろ朝ですね。",
            (4, 0): "5時です。もうすぐ起きてくるかな？",
            (6, 0): "6時です。おはようございます。",
            (7, 0): "7時です。おはようございます。",
            (8, 0): "8時です。学校か仕事に行く時間かな？",
            (9, 0): "9時です。授業1時間目がもうすぐ終わるかな？",
            (10, 0): "10時です。今は何してるのかなぁ・・？",
            (11, 0): "11時です。もうすぐお昼です。何食べるのかな？",
            (12, 0): "12時です。昼ご飯の時間です。何食べるの？",
            (13, 0): "13時です。昼休みの時間かな？",
            (14, 0): "14時です。眠いですね。",
            (15, 0): "15時です。そろそろおやつの時間ですね。",
            (16, 0): "16時です。暗くなってきたかな？",
            (17, 0): "17時です。放課後です。何をしますか？",
            (18, 0): "18時です。夜ごはんの時間かな？",
            (19, 0): "19時です。お風呂入るのかな？",
            (20, 0): "20時です。そろそろ寝るの？それとも勉強？それとも？",
            (21, 0): "21時です。そろそろ眠くなってきました。",
            (22, 0): "22時です。そろそろVCするかな？",
            (23, 0): "23時です。もう寝る時間です。おやすみなさい。",
            (23, 40): "23時40分です。おやすみなさい。",
            (23, 58): "23時58分です。もうすぐあけおめ？()",
        }

        self.random_odai = [
            "昨日、何食べた？", "今日、何食べた？", "今日、もしくは明日何をする予定？", "明日は何をするの？",
            "好きなものは何？", "好きな食べ物は何？", "好きなゲームは何？", "いつも何時に寝てるの？"
        ]

    async def cog_load(self):
        self.time_signal_loop.start()
        print("TimeSignalCogがロードされました。タスクを開始します。")

    async def cog_unload(self):
        self.time_signal_loop.stop()
        print("TimeSignalCogがアンロードされました。タスクを停止します。")

    @tasks.loop(seconds=60)
    async def time_signal_loop(self):
        now = datetime.datetime.now()
        if (now.hour, now.minute) in self.messages:

            db = self.bot.async_db["Main"].TimeSignal

            async for channel in db.find():
                try:
                    ch = self.bot.get_channel(channel.get("Channel", None))
                    if not ch:
                        continue
                    await ch.send(embeds=[discord.Embed(title="時報", description=self.messages[(now.hour, now.minute)], color=discord.Color.blue()), discord.Embed(title="お題", description=random.choice(self.random_odai), color=discord.Color.blue())])
                    await asyncio.sleep(1)
                except:
                    continue

            print("時報を送信しました。")

    @commands.hybrid_group(name="time-signal", description="時報・お題を通知するチャンネルを設定します。", fallback="setting")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def time_signal_setting(self, ctx: commands.Context, チャンネル: discord.TextChannel = None):
        db = self.bot.async_db["Main"].TimeSignal
        if  チャンネル:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Channel": チャンネル.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="時報チャンネルを設定しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await db.delete_one(
                {"Guild": ctx.guild.id}
            )
            await ctx.reply(embed=discord.Embed(title="時報チャンネルを削除しました。", color=discord.Color.red()), ephemeral=True)

    def get_closest_message(self):
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute

        valid_times = [
            (hour, minute) for (hour, minute) in self.messages
            if hour * 60 + minute <= current_minutes
        ]

        if not valid_times:
            closest = max(self.messages.keys())
        else:
            closest = max(valid_times, key=lambda t: t[0] * 60 + t[1])

        return self.messages[closest]

    @time_signal_setting.command(name="send", description="このチャンネルに一時的に一番近い時報とお題を表示します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def time_signal_send(self, ctx: commands.Context):
        await ctx.reply(embeds=[discord.Embed(title="時報", description=self.get_closest_message(), color=discord.Color.blue()),
                                discord.Embed(title="お題", description=random.choice(self.random_odai), color=discord.Color.blue())])

async def setup(bot):
    await bot.add_cog(TimeSignalCog(bot))