from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
from urllib.parse import quote
import re
from functools import partial
import time

class ShareCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ShareCog")

    async def message_autocomplete_share(self, interaction: discord.Interaction, current: str):
        try:
            messages = []
            async for m in interaction.channel.history(limit=50):
                messages.append(m)
            choices = []

            for message in messages:
                if message.content == "":
                    continue
                if current.lower() in message.content.lower():
                    choices.append(discord.app_commands.Choice(name=message.content[:100], value=str(message.id)))

                if len(choices) >= 25:
                    break

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @commands.hybrid_group(name="share", description="xにシェアをします。", fallback="twitter")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @discord.app_commands.autocomplete(メッセージ=message_autocomplete_share)
    async def share_twitter(self, ctx: commands.Context, メッセージ: str):
        await ctx.defer(ephemeral=True)
        try:
            メッセージ_ = await ctx.channel.fetch_message(int(メッセージ))
        except:
            return await ctx.reply(embed=discord.Embed(title="メッセージが見つかりません", color=discord.Color.red()), ephemeral=True)
        await ctx.reply(embed=discord.Embed(title="X(旧Twitter)にシェアする", description=f"{メッセージ_.author.display_name}さんの発言:\n{メッセージ_.content}", color=discord.Color.blue()), ephemeral=True, view=discord.ui.View().add_item(discord.ui.Button(label="シェアする", url=f"https://twitter.com/intent/tweet?text={quote(f"{メッセージ_.author.display_name}さんの発言:\n" + メッセージ_.content)}")))

    @share_twitter.command(name="discord", description="Discordチャンネルにシェアします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @discord.app_commands.autocomplete(メッセージ=message_autocomplete_share)
    async def share_discord(self, ctx: commands.Context, チャンネル: discord.TextChannel, メッセージ: str):
        await ctx.defer(ephemeral=True)
        try:
            メッセージ_ = await ctx.channel.fetch_message(int(メッセージ))
        except:
            return await ctx.reply(embed=discord.Embed(title="メッセージが見つかりません", color=discord.Color.red()), ephemeral=True)
        await チャンネル.send(embed=discord.Embed(title=f"{ctx.author.display_name}がシェアしました。", description=f"{メッセージ_.author.display_name}さんの発言:\n{メッセージ_.content}", color=discord.Color.blue()))
        await ctx.reply(embed=discord.Embed(title="Discordチャンネルにシェアしました。", color=discord.Color.green()), ephemeral=True)

    @share_twitter.command(name="line", description="Lineにシェアします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @discord.app_commands.autocomplete(メッセージ=message_autocomplete_share)
    async def share_line(self, ctx: commands.Context, メッセージ: str):
        await ctx.defer(ephemeral=True)
        try:
            メッセージ_ = await ctx.channel.fetch_message(int(メッセージ))
        except:
            return await ctx.reply(embed=discord.Embed(title="メッセージが見つかりません", color=discord.Color.red()), ephemeral=True)
        await ctx.reply(embed=discord.Embed(title="Lineにシェアする", description=f"{メッセージ_.author.display_name}さんの発言:\n{メッセージ_.content}", color=discord.Color.green()), ephemeral=True, view=discord.ui.View().add_item(discord.ui.Button(label="シェアする", url=f"https://line.me/R/msg/text/?{quote(f"{メッセージ_.author.display_name}さんの発言:\n" + メッセージ_.content)}")))

async def setup(bot):
    await bot.add_cog(ShareCog(bot))