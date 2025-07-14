from discord.ext import commands
import datetime
import discord
import traceback
import sys
import logging
import random
from discord import app_commands
import time
import asyncio
import re
from functools import partial
import time

class ChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> ChannelCog")

    @commands.hybrid_group(name="channel", description="チャンネルを作成します。", fallback="create")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    @app_commands.choices(種類=[
        app_commands.Choice(name='テキストチャンネル',value="text"),
        app_commands.Choice(name='ボイスチャンネル',value="voice"),
        app_commands.Choice(name='カテゴリチャンネル',value="cat"),
    ])
    async def channel_create(self, ctx: commands.Context, チャンネル名: str, 種類: app_commands.Choice[str], カテゴリ: discord.CategoryChannel = None):
        try:
            await ctx.defer()
            if 種類.value == "text":
                if カテゴリ:
                    c = await カテゴリ.create_text_channel(name=チャンネル名, reason=f"{ctx.author.name}により作成")
                else:
                    c = await ctx.guild.create_text_channel(name=チャンネル名, reason=f"{ctx.author.name}により作成")
            elif 種類.value == "voice":
                if カテゴリ:
                    c = await カテゴリ.create_voice_channel(name=チャンネル名, reason=f"{ctx.author.name}により作成")
                else:
                    c = await ctx.guild.create_voice_channel(name=チャンネル名, reason=f"{ctx.author.name}により作成")
            elif 種類.value == "cat":
                if カテゴリ:
                    return await ctx.reply(embed=discord.Embed(title="カテゴリ内にカテゴリは作成できません。", color=discord.Color.red()))
                else:
                    c = await ctx.guild.create_category(name=チャンネル名)
            await ctx.reply(embed=discord.Embed(title="チャンネルを作成しました。", color=discord.Color.green(), description=f"{c.mention}"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="チャンネルを作成できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @channel_create.command(name="info", description="チャンネルの情報を表示するよ")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def channel_info(self, ctx: commands.Context, チャンネル: str = None):
        await ctx.defer()
        if チャンネル:
            channel = await ctx.guild.fetch_channel(int(チャンネル))
        else:
            channel = ctx.channel
        embed = discord.Embed(title="チャンネルの情報", color=discord.Color.green())
        embed.add_field(name="名前", value=channel.name, inline=False)
        embed.add_field(name="ID", value=str(channel.id), inline=False)
        if channel.category:
            embed.add_field(name="カテゴリ", value=channel.category.name, inline=False)
        else:
            embed.add_field(name="カテゴリ", value="なし", inline=False)
        embed.add_field(name="位置", value=str(channel.position), inline=False)
        embed.add_field(name="メンション", value=channel.mention, inline=False)
        embed.set_footer(text=f"{channel.guild.name} / {channel.guild.id}")
        await ctx.reply(embed=embed)

    @channel_create.command(name="lock", description="このチャンネルをロックします。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def lock_channel_(self, ctx: commands.Context):
        try:
            await ctx.defer()
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            overwrite.create_polls = False
            overwrite.create_public_threads = False
            overwrite.create_private_threads = False
            overwrite.use_application_commands = False
            overwrite.attach_files = False
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.reply(embed=discord.Embed(title="チャンネルをロックしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="チャンネルをロックできませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @channel_create.command(name="unlock", description="このチャンネルのロックを解除します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def unlock_channel_(self, ctx: commands.Context):
        try:
            await ctx.defer()
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            overwrite.create_polls = True
            overwrite.create_public_threads = True
            overwrite.create_private_threads = True
            overwrite.use_application_commands = True
            overwrite.attach_files = True
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.reply(embed=discord.Embed(title="チャンネルを解放しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="チャンネルを解放できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @channel_create.command(name="private", description="このチャンネルをプライベートチャンネルにします。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def private_channel(self, ctx: commands.Context):
        try:
            await ctx.defer()
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.read_messages = False
            if type(ctx.channel) == discord.VoiceChannel:
                overwrite.connect = False
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.reply(embed=discord.Embed(title="プライベートチャンネルにしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="プライベートチャンネルにできませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @channel_create.command(name="unprivate", description="このチャンネルのプライベートチャンネルを解除します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def unprivate_channel(self, ctx: commands.Context):
        try:
            await ctx.defer()
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.read_messages = True
            if type(ctx.channel) == discord.VoiceChannel:
                overwrite.connect = True
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.reply(embed=discord.Embed(title="プライベートチャンネルを解除しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="プライベートチャンネルを解除できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @channel_create.command(name="slowmode", description="このチャンネルに低速モードを付けます。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def channel_slowmode(self, ctx: commands.Context, 何秒か: int):
        try:
            await ctx.defer()
            await ctx.channel.edit(slowmode_delay=何秒か)
            await ctx.reply(embed=discord.Embed(title="スローモードを設定しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="スローモードを設定できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @channel_create.command(name="server-archive", description="サーバーを永久凍結するよ")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def server_archive(self, ctx: commands.Context):
        try:
            await ctx.defer()
            try:
                rule = await ctx.guild.fetch_automod_rules()
                for r in rule:
                    try:
                        await r.delete()
                    except:
                        continue
                    await asyncio.sleep(1)
            except:
                pass
            await ctx.guild.create_automod_rule(
                name="アーカイブ用",
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.member_profile, regex_patterns=["."], allow_list=[f"{ctx.guild.me.display_name}"]),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_member_interactions
                    )
                ],
                exempt_roles=[ctx.guild.me.top_role],
                enabled=True
            )
            await ctx.reply(embed=discord.Embed(title="サーバーをアーカイブしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="サーバーをアーカイブできませんでした。", color=discord.Color.red(), description=f"権限エラーです。\n{e}"))
        
    @channel_create.command(name="server-remove-archive", description="サーバーの永久凍結を解除するよ")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def server_remove_archive(self, ctx: commands.Context):
        await ctx.defer()
        rule = await ctx.guild.fetch_automod_rules()
        for r in rule:
            if r.name == "アーカイブ用":
                await r.delete()
                return await ctx.reply(embed=discord.Embed(title="アーカイブを解除しました。", color=discord.Color.green()))
        return await ctx.reply(embed=discord.Embed(title="アーカイブを解除できませんでした。", color=discord.Color.red(), description=f"まだアーカイブされていません。"))

async def setup(bot):
    await bot.add_cog(ChannelCog(bot))