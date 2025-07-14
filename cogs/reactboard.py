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

cooldown_reaction = {}

class ReactionBoardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ReactionBoardCog")

    async def get_reaction_channel(self, guild: discord.Guild, emoji: str):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one({"Guild": guild.id, "Emoji": emoji}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind["Channel"])
    
    async def get_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind["Channel"])

    async def save_message(self, message: discord.Message, msg: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        await db.replace_one(
            {"Guild": message.guild.id}, 
            {"Guild": message.guild.id, "ID": message.id, "ReactMessageID": msg.id}, 
            upsert=True
        )

    async def read_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "ReactMessageID": message.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind["ID"]

    async def reaction_add(self, message: discord.Message, emoji_: str):
        reaction_counts = {}
        for reaction in message.reactions:
            emoji = reaction.emoji
            count = reaction.count
            reaction_counts[emoji] = count
        if reaction_counts:
            for emoji, count in reaction_counts.items():
                if emoji == emoji_:
                    if count == 1:
                        cha = await self.get_reaction_channel(message.guild, emoji_)
                        msg = await cha.send(embed=discord.Embed(title=f"{emoji}x1", description=f"{message.content}", color=discord.Color.blue()).set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url), view=discord.ui.View().add_item(discord.ui.Button(label="メッセージに飛ぶ", url=message.jump_url)))
                        await self.save_message(msg, message)
                    else:
                        cha = await self.get_channel(message.guild)
                        msg = await self.read_message(message)
                        try:
                            m = await cha.fetch_message(msg)
                        except:
                            return
                        msg = await m.edit(embed=discord.Embed(title=f"{emoji}x{count}", description=f"{message.content}", color=discord.Color.blue()).set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url))
                    return
                
    async def reaction_add_2(self, message: discord.Message, emoji_: str):
        reaction_counts = {}
        for reaction in message.reactions:
            emoji = reaction.emoji
            count = reaction.count
            reaction_counts[emoji] = count
        if reaction_counts:
            for emoji, count in reaction_counts.items():
                if emoji == emoji_:
                    cha = await self.get_channel(message.guild)
                    msg = await self.read_message(message)
                    try:
                        m = await cha.fetch_message(msg)
                    except:
                        return
                    msg = await m.edit(embed=discord.Embed(title=f"{emoji}x{count}", description=f"{message.content}", color=discord.Color.blue()).set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url))
                    return

    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add_reaction_board(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        check = await self.get_reaction_channel(reaction.message.guild, reaction.emoji)
        if check:
            current_time = time.time()
            last_message_time = cooldown_reaction.get(reaction.message.guild.id, 0)
            if current_time - last_message_time < 1:
                return
            cooldown_reaction[reaction.message.guild.id] = current_time
            await self.reaction_add(reaction.message, reaction.emoji)

    @commands.Cog.listener("on_reaction_remove")
    async def on_reaction_remove_reaction_board(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        check = await self.get_reaction_channel(reaction.message.guild, reaction.emoji)
        if check:
            current_time = time.time()
            last_message_time = cooldown_reaction.get(reaction.message.guild.id, 0)
            if current_time - last_message_time < 1:
                return
            cooldown_reaction[reaction.message.guild.id] = current_time
            await self.reaction_add_2(reaction.message, reaction.emoji)

    async def set_reaction_board(self, ctx: commands.Context, チャンネル: discord.TextChannel, 絵文字: str):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.replace_one(
            {"Guild": ctx.guild.id, "Emoji": 絵文字, "Channel": チャンネル.id}, 
            {"Guild": ctx.guild.id, "Channel": チャンネル.id, "Emoji": 絵文字}, 
            upsert=True
        )

    async def delete_reaction_board(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.delete_one({"Guild": ctx.channel.id})

    @commands.hybrid_group(name="reactionboard", description="リアクションボードをセットアップします。", fallback="setup")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def reactionboard_setup(self, ctx: commands.Context, チャンネル: discord.TextChannel, 絵文字: str):
        try:
            await ctx.defer()
            await self.set_reaction_board(ctx, チャンネル, 絵文字)
            await ctx.reply(embed=discord.Embed(title="リアクションボードをセットアップしました。", color=discord.Color.green(), description=f"{チャンネル.mention}"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="リアクションボードをセットアップできませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @reactionboard_setup.command(name="disable", description="リアクションボードを無効にします。")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def reation_board_disable(self, ctx: commands.Context):
        try:
            await ctx.defer()
            await self.delete_reaction_board(ctx)
            await ctx.reply(embed=discord.Embed(title="リアクションボードを無効にしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="リアクションボードを無効にできませんでした。", color=discord.Color.red(), description="権限エラーです。"))

async def setup(bot):
    await bot.add_cog(ReactionBoardCog(bot))