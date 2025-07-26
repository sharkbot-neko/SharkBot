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
import requests
from bs4 import BeautifulSoup
import time
import random

cooldown_eventalert = {}

class AlertCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_mention(self, guild: discord.Guild, channel_id: int):
        db = self.bot.async_db["Main"].AlertMention
        try:
            dbfind = await db.find_one({"Channel": channel_id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return guild.get_role(dbfind.get("Role")).mention

    @commands.Cog.listener("on_scheduled_event_create")
    async def on_scheduled_event_create_alert(self, event: discord.ScheduledEvent):
        db = self.bot.async_db["Main"].EventAlert
        try:
            dbfind = await db.find_one({"Guild": event.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_eventalert.get(event.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_eventalert[event.guild.id] = current_time
        try:
            ch = await event.guild.fetch_channel(dbfind.get("Channel"))
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="確認する", url=event.url))
            men = await self.get_mention(event.guild, ch.id)
            if not men:
                await ch.send(embed=discord.Embed(title="イベントが作成されました！", description=f"{event.name}", color=discord.Color.green())
                          .add_field(name="開始時刻", value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}").set_footer(text=f"{event.guild.name} / {event.guild.id}", icon_url=event.guild.icon.url if event.guild.icon else self.bot.user.avatar.url), view=view)
                return
            await ch.send(content=men, embed=discord.Embed(title="イベントが作成されました！", description=f"{event.name}", color=discord.Color.green())
                          .add_field(name="開始時刻", value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}").set_footer(text=f"{event.guild.name} / {event.guild.id}", icon_url=event.guild.icon.url if event.guild.icon else self.bot.user.avatar.url), view=view)
        except:
            return

    @commands.hybrid_group(name="alert", description="イベントを通知するチャンネルを設定します。", fallback="event")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def alert_event(self, ctx: commands.Context, チャンネル: discord.TextChannel = None):
        db = self.bot.async_db["Main"].EventAlert
        if  チャンネル:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Channel": チャンネル.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="イベント作成時に通知するチャンネルを設定しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await db.delete_one(
                {"Guild": ctx.guild.id}
            )
            await ctx.reply(embed=discord.Embed(title="イベント作成時に通知するチャンネルを削除しました。", color=discord.Color.red()), ephemeral=True)

    @alert_event.command(name="mention", description="アラート時にメンションするロールを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def alert_mention(self, ctx: commands.Context, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].AlertMention
        if not ロール:
            await db.delete_one(
                {"Channel": ctx.channel.id}
            )
            return await ctx.reply(embed=discord.Embed(title="アラート時にメンションしなくしました。", color=discord.Color.green()))
        await db.replace_one(
            {"Channel": ctx.channel.id},
            {"Channel": ctx.channel.id, "Role": ロール.id},
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="アラート時にメンションするようにしました。", description=f"{ロール.mention}", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(AlertCog(bot))