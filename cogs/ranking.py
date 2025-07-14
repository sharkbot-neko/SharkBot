from discord.ext import commands, tasks
import discord
import traceback
import sys
import logging
from discord import app_commands
import random
import numpy as np
import matplotlib.pyplot as plt
import io
import logging
import time
import asyncio
import MeCab
import re
from functools import partial
import time

logger = logging.getLogger(__name__)

def parse(text):
    words = []
    tagger = MeCab.Tagger()
    node = tagger.parseToNode(text)
    while node:
        features = node.feature.split(',')
        if features[0] == "名詞":
            words.append(node.surface)
        node = node.next

    return words

async def async_parse(text):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, parse, text)

async def get_ban_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].BANRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["ban_count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_message_delete_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].MessageDeleteRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["delete_count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_message_edit_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].MessageEditRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["edit_count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_command_run_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].CommandRunRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["run_count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_disboard_bump_run_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].BumpRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["bump_count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_mention_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].MentionRanking
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["count"]
        except Exception as e:
            return 0
    except:
        return 0
    
async def get_sharkpoint_count(interaction: discord.Interaction, user: discord.User):
    try:
        db = interaction.client.async_db["Main"].SharkBotInstallPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
            return dbfind["count"]
        except Exception as e:
            return 0
    except:
        return 0

class RankingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_ranking_tag.start()
        print(f"init -> RankingCog")

    def cog_unload(self):
        self.check_ranking_tag.stop()

    @commands.Cog.listener("on_member_ban")
    async def on_member_ban_ranking(self, guild: discord.Guild, user: discord.User):
        db = self.bot.async_db["Main"].BANRanking
        user_data = await db.find_one({"_id": user.id})
        if user_data:
            await db.update_one(
                {"_id": user.id},
                {"$inc": {"ban_count": 1}, "$set": {"Name": user.display_name, "Avatar": user.avatar.url if user.avatar else user.default_avatar.url}}
            )
        else:
            await db.insert_one({"_id": user.id, "Name": user.display_name, "ban_count": 1, "Avatar": user.avatar.url if user.avatar else user.default_avatar.url})

    @commands.Cog.listener("on_interaction")
    async def on_interaction_commandranking_ranking(self, interaction : discord.Interaction):
        db = self.bot.async_db["Main"].CommandRunRanking
        user_data = await db.find_one({"_id": interaction.user.id})
        if user_data:
            await db.update_one({"_id": interaction.user.id}, {"$inc": {"run_count": 1}})
        else:
            await db.insert_one({"_id": interaction.user.id, "run_count": 1})

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_ranking(self, message: discord.Message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].MessageDeleteRanking
        user_data = await db.find_one({"_id": message.author.id})
        if user_data:
            await db.update_one({"_id": message.author.id}, {"$inc": {"delete_count": 1}})
        else:
            await db.insert_one({"_id": message.author.id, "delete_count": 1})

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_ranking(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return
        db = self.bot.async_db["Main"].MessageEditRanking
        user_data = await db.find_one({"_id": after.author.id})
        if user_data:
            await db.update_one({"_id": after.author.id}, {"$inc": {"edit_count": 1}})
        else:
            await db.insert_one({"_id": after.author.id, "edit_count": 1})

    @commands.Cog.listener("on_message")
    async def on_message_bump_disboard_ranking(self, message: discord.Message):
        if message.author.id == 302050872383242240:
            try:
                if "表示順をアップ" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].BumpRanking
                    user_data = await db.find_one({"_id": message.interaction_metadata.user.id})
                    if user_data:
                        await db.update_one({"_id": message.interaction_metadata.user.id}, {"$inc": {"bump_count": 1}})
                    else:
                        await db.insert_one({"_id": message.interaction_metadata.user.id, "bump_count": 1})
            except:
                return
            
    @commands.Cog.listener("on_message")
    async def on_message_ranking_mention(self, message: discord.Message):
        if message.author.bot:
            return
        if message.mentions:
            db = self.bot.async_db["Main"].MentionRanking
            user_data = await db.find_one({"_id": message.author.id})
            if user_data:
                await db.update_one({"_id": message.author.id}, {"$inc": {"count": 1}})
            else:
                await db.insert_one({"_id": message.author.id, "count": 1})

    async def top_add_tag(self, db_: str, count: str, 称号: str):
        db = self.bot.async_db["Main"][db_]
        shou_db = self.bot.async_db["Main"].UserTag
        top_users = await db.find().sort(f"{count}", -1).limit(10).to_list(length=10)
        await db.delete_many({"Tag": 称号})
        for index, user_data in enumerate(top_users, start=1):
            try:
                await shou_db.replace_one(
                    {"User": user_data["_id"]},
                    {"User": user_data["_id"], "Tag": 称号},
                    upsert=True
                )
            except:
                continue
        return True

    @tasks.loop(minutes=5)
    async def check_ranking_tag(self):
        rankings = [
            ("BANRanking", "ban_count", "出禁王者"),
            ("CommandRunRanking", "run_count", "指示王者"),
            ("MessageDeleteRanking", "delete_count", "撤回王者"),
            ("MessageEditRanking", "edit_count", "編集王者"),
            ("BumpRanking", "bump_count", "鯖揚漁師"),
            ("MentionRanking", "count", "召喚王者"),
        ]

        for db_, b, 称号 in rankings:
            try:
                await self.top_add_tag(db_, b, 称号)
            except Exception as e:
                logger.error(f"{db_} の処理中にエラー: {e}")

    @commands.hybrid_command(name="ranking", description="様々なランキングを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(項目=[
        app_commands.Choice(name='BAN回数',value="ban"),
        app_commands.Choice(name='コマンド実行回数',value="commands"),
        app_commands.Choice(name='メッセージ削除回数',value="delete"),
        app_commands.Choice(name='メッセージ編集回数',value="edit"),
        app_commands.Choice(name='DisboardBump回数',value="bump"),
        app_commands.Choice(name='メンション回数',value="mention"),
        app_commands.Choice(name='ポイント億万長者',value="point"),
        app_commands.Choice(name='私の統計',value="mycount"),
    ])
    async def setting_ranking(self, ctx: commands.Context, 項目: app_commands.Choice[str]):
        val = 項目.value
        if val == "ban":
            db = self.bot.async_db["Main"].BANRanking
            top_users = await db.find().sort("ban_count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="BAN回数", color=discord.Color.green(), description="まだBANされていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                ban_count = user_data["ban_count"]
                member = self.bot.get_user(user_id)
                username = f"{member.name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {ban_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> BAN回数", color=discord.Color.green(), description=ranking_message))
        elif val == "commands":
            db = self.bot.async_db["Main"].CommandRunRanking
            top_users = await db.find().sort("run_count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="コマンド実行回数", color=discord.Color.green(), description="まだ実行されていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                run_count = user_data["run_count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {run_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> コマンド実行回数", color=discord.Color.green(), description=ranking_message))
        elif val == "delete":
            db = self.bot.async_db["Main"].MessageDeleteRanking
            top_users = await db.find().sort("delete_count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="メッセージ削除回数", color=discord.Color.green(), description="まだ削除されていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["delete_count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> メッセージ削除回数", color=discord.Color.green(), description=ranking_message))
        elif val == "edit":
            db = self.bot.async_db["Main"].MessageEditRanking
            top_users = await db.find().sort("edit_count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="メッセージ編集回数", color=discord.Color.green(), description="まだ編集されていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["edit_count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> メッセージ編集回数", color=discord.Color.green(), description=ranking_message))
        elif val == "bump":
            db = self.bot.async_db["Main"].BumpRanking
            top_users = await db.find().sort("bump_count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="DisboardBump回数", color=discord.Color.green(), description="まだBumpされていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["bump_count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> DisboardBump回数", color=discord.Color.green(), description=ranking_message))
        elif val == "mention":
            db = self.bot.async_db["Main"].MentionRanking
            top_users = await db.find().sort("count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="メンション回数", color=discord.Color.green(), description="まだメンションされていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> メンション回数", color=discord.Color.green(), description=ranking_message))
        elif val == "point":
            db = self.bot.async_db["Main"].SharkBotInstallPoint
            top_users = await db.find().sort("count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await ctx.reply(embed=discord.Embed(title="ポイント所持数", color=discord.Color.green(), description="まだポイントが所持されていません。"))
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["count"]
                member = self.bot.get_user(user_id)
                username = f"{member.display_name} ({user_id})" if member else f"Unknown ({user_id})"
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ポイント所持数", color=discord.Color.green(), description=ranking_message))
        elif val == "mycount":
            await ctx.defer()
            ban_count = await get_ban_count(ctx.interaction, ctx.author)
            message_delete_count = await get_message_delete_count(ctx.interaction, ctx.author)
            message_edit_count = await get_message_edit_count(ctx.interaction, ctx.author)
            command_run_count = await get_command_run_count(ctx.interaction, ctx.author)
            bump_disboard_count = await get_disboard_bump_run_count(ctx.interaction, ctx.author)
            men = await get_mention_count(ctx.interaction, ctx.author)
            point = await get_sharkpoint_count(ctx.interaction, ctx.author)
            def draw(ban_count, message_delete_count, message_edit_count, bump_disboard_count, command_run_count, point):
                labels_event = ['BAN', 'MessageDelete', 'MessageEdit', 'Bump', 'SharkPoint']
                means_event = [ban_count, message_delete_count, message_edit_count, bump_disboard_count, point]

                x_event = np.arange(len(labels_event))
                width_event = 0.4

                fig, (ax1) = plt.subplots(1, figsize=(12, 6))

                rect1 = ax1.bar(x_event, means_event, width_event)
                ax1.set_xticks(x_event)
                ax1.set_xticklabels(labels_event)
                ax1.set_ylabel('Counts')
                ax1.set_title('Event Counts')

                sio = io.BytesIO()
                plt.savefig(sio, format="png")
                sio.seek(0)
                return sio
            grap = await asyncio.to_thread(draw, ban_count, message_delete_count, message_edit_count, bump_disboard_count, command_run_count, point)
            await ctx.reply(file=discord.File(grap, "data.png"), embed=discord.Embed(title=f"`{ctx.author.name}`さんの統計", color=discord.Color.blue(), description=f"""BAN回数: {ban_count}回
メッセージ削除回数: {message_delete_count}回
メッセージ編集回数: {message_edit_count}回
DisboardのBump回数: {bump_disboard_count}回
コマンド実行回数: {command_run_count}回
メンション回数: {men}回
Sharkポイント所持数: {point}ポイント
"""))

    @commands.command(name="sync_ban_username")
    async def sync_ban_username(self, ctx: commands.Context):
        if not ctx.author.id == 1335428061541437531:
            return
        db = self.bot.async_db["Main"].BANRanking
        async for d in db.find({}):
            if self.bot.get_user(d["_id"]):
                await db.replace_one(
                    {"_id": d["_id"]},
                    {"_id": d["_id"], "ban_count": d["ban_count"], "Name": self.bot.get_user(d["_id"]).display_name if self.bot.get_user(d["_id"]) else f"{d["_id"]}", "Avatar": self.bot.get_user(d["_id"]).avatar.url if self.bot.get_user(d["_id"]).avatar else self.bot.get_user(d["_id"]).default_avatar.url},
                    upsert=True
                )
            else:
                await db.replace_one(
                    {"_id": d["_id"]},
                    {"_id": d["_id"], "ban_count": d["ban_count"], "Name": self.bot.get_user(d["_id"]).display_name if self.bot.get_user(d["_id"]) else f"{d["_id"]}", "Avatar": "https://cdn.discordapp.com/embed/avatars/0.png"},
                    upsert=True
                )
        await ctx.message.add_reaction("✅")

@app_commands.context_menu(name="統計")
async def user_status(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    ban_count = await get_ban_count(interaction, member)
    message_delete_count = await get_message_delete_count(interaction, member)
    message_edit_count = await get_message_edit_count(interaction, member)
    command_run_count = await get_command_run_count(interaction, member)
    bump_disboard_count = await get_disboard_bump_run_count(interaction, member)
    men = await get_mention_count(interaction, member)
    point = await get_sharkpoint_count(interaction, member)
    def draw(ban_count, message_delete_count, message_edit_count, bump_disboard_count, command_run_count, point):
        labels_event = ['BAN', 'MessageDelete', 'MessageEdit', 'Bump', 'SharkPoint']
        means_event = [ban_count, message_delete_count, message_edit_count, bump_disboard_count, point]

        x_event = np.arange(len(labels_event))
        width_event = 0.4

        fig, (ax1) = plt.subplots(1, figsize=(12, 6))

        rect1 = ax1.bar(x_event, means_event, width_event)
        ax1.set_xticks(x_event)
        ax1.set_xticklabels(labels_event)
        ax1.set_ylabel('Counts')
        ax1.set_title('Event Counts')

        sio = io.BytesIO()
        plt.savefig(sio, format="png")
        sio.seek(0)
        return sio
    grap = await asyncio.to_thread(draw, ban_count, message_delete_count, message_edit_count, bump_disboard_count, command_run_count, point)
    await interaction.followup.send(file=discord.File(grap, "data.png"), embed=discord.Embed(title=f"`{member.name}`さんの統計", color=discord.Color.blue(), description=f"""BAN回数: {ban_count}回
メッセージ削除回数: {message_delete_count}回
メッセージ編集回数: {message_edit_count}回
DisboardのBump回数: {bump_disboard_count}回
コマンド実行回数: {command_run_count}回
メンション回数: {men}回
Sharkポイント所持数: {point}ポイント
"""))

async def setup(bot):
    await bot.add_cog(RankingCog(bot))
    bot.tree.add_command(user_status)