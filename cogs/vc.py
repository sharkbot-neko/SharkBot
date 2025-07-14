from discord.ext import commands
import datetime
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

cooldown_tempvc = {}

class VCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> VCCog")

    @commands.hybrid_group(name="vc", description="VCにメンバーを移動させます。", fallback="move")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def vc_move(self, ctx: commands.Context, メンバー: discord.Member, チャンネル: discord.VoiceChannel = None):
        try:
            await ctx.defer()
            if not チャンネル:
                if not ctx.author.voice:
                    return await ctx.reply(embed=discord.Embed(title=f"移動させる先が見つかりません。", color=discord.Color.green()))
                await メンバー.edit(voice_channel=ctx.author.voice.channel)
            else:
                await メンバー.edit(voice_channel=チャンネル)
            await ctx.reply(embed=discord.Embed(title=f"メンバーを移動しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="メンバーを移動できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @vc_move.command(name="leave", description="VCからメンバーを退出させます。")
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_leave(self, ctx: commands.Context, メンバー: discord.Member):
        try:
            await ctx.defer()
            await メンバー.edit(voice_channel=None)
            await ctx.reply(embed=discord.Embed(title="メンバーを退出させました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="メンバーを退出させれませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @vc_move.command(name="bomb", description="VCを解散させます。")
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_bomb(self, ctx: commands.Context, チャンネル: discord.VoiceChannel = None):
        try:
            await ctx.defer()
            if not チャンネル:
                if not ctx.author.voice:
                    return await ctx.reply(embed=discord.Embed(title=f"解散させるvcが見つかりません。", color=discord.Color.green()))
                for chm in ctx.author.voice.channel.members:
                    await chm.edit(voice_channel=None)
                    await asyncio.sleep(1)
            else:
                for chm in チャンネル.members:
                    await chm.edit(voice_channel=None)
                    await asyncio.sleep(1)
            await ctx.reply(embed=discord.Embed(title="VCを解散させました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="VCを解散できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @vc_move.command(name="gather", description="VCに参加している全員を特定のVCに集めます。")
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_gather(self, ctx: commands.Context, チャンネル: discord.VoiceChannel = None):
        try:
            await ctx.defer()
            if not チャンネル:
                if not ctx.author.voice:
                    return await ctx.reply(embed=discord.Embed(title=f"集めたいVCが見つかりません。", color=discord.Color.green()))
                for vc in ctx.guild.voice_channels:
                    for vm in vc.members:
                        await vm.edit(voice_channel=ctx.author.voice.channel)
                        await asyncio.sleep(1)
            else:
                for vc in ctx.guild.voice_channels:
                    for vm in vc.members:
                        await vm.edit(voice_channel=チャンネル)
                        await asyncio.sleep(1)
            await ctx.reply(embed=discord.Embed(title="VCに集めました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="VCに集められませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @vc_move.command(name="youtube", description="discordでyoutubeの見れるリンクを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_youtube(self, ctx: commands.Context):
        await ctx.reply(content="Youtubeを見れる招待リンク\nhttps://discord.com/activities/880218394199220334")

    @vc_move.command(name="whiteboard", description="discordでホワイトボードが使えるリンクを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_whiteboard(self, ctx: commands.Context):
        await ctx.reply(content="ホワイトボードが使える招待リンク\nhttps://discord.com/activities/1070087967294631976")

    async def set_tempvc(self, guild: discord.Guild, vc: discord.VoiceChannel = None):
        db = self.bot.async_db["Main"].TempVCBeta
        if not vc:
            await db.delete_one({"Guild": guild.id})
            return True
        await db.replace_one(
            {"Guild": guild.id}, 
            {"Guild": guild.id, "Channel": vc.id}, 
            upsert=True
        )
        return True

    @vc_move.command(name="temp", description="一時的なボイスチャンネルを作成するボイスチャンネルを作成します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def vc_temp(self, ctx: commands.Context, チャンネル: discord.VoiceChannel = None):
        await ctx.defer()
        await self.set_tempvc(ctx.guild, チャンネル)
        if not チャンネル:
            return await ctx.reply(embed=discord.Embed(title="一時的なVCを削除しました。", color=discord.Color.red()))
        await ctx.reply(embed=discord.Embed(title="一時的なVCを設定しました。", color=discord.Color.green()))

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_temp(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        db = self.bot.async_db["Main"].TempVCBeta
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try: 
            if not after.channel.id == dbfind.get("Channel", 0):
                return
            current_time = time.time()
            last_message_time = cooldown_tempvc.get(member.guild.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_tempvc[member.guild.id] = current_time
            await asyncio.sleep(1)
            if after.channel.category:
                vc = await after.channel.category.create_voice_channel(name=f"tempvc-{member.name}")
            else:
                vc = await member.guild.create_voice_channel(name=f"tempvc-{member.name}")
            await asyncio.sleep(2)
            await member.edit(voice_channel=vc)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="削除", style=discord.ButtonStyle.red, custom_id="tempvc_remove"))
            await vc.send(embed=discord.Embed(title="一時的なVCの管理パネル", color=discord.Color.blue()), view=view)
        except:
            return

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel_vc(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "tempvc_remove":
                    await interaction.response.defer(ephemeral=True)
                    await interaction.channel.delete(reason="一時的なVCチャンネルの削除のため。")
        except:
            return

async def setup(bot):
    await bot.add_cog(VCCog(bot))