from discord.ext import commands
import discord
import traceback
import sys
import logging
import yt_dlp
import random
import pykakasi
import struct 
import io
import aiohttp
from datetime import datetime, timedelta
import time
import string
import datetime
import asyncio

COOLDOWN_TIME = 5
user_last_message_time = {}

cooldown_backup_time = {}

class userNoteClear(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.green)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if self.member.id != interaction.user.id:
            return
        await interaction.message.edit(embed=discord.Embed(title="キャンセルしました。", color=discord.Color.green()), view=None)

    @discord.ui.button(label="はい", style=discord.ButtonStyle.red)
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if self.member.id != interaction.user.id:
            return
        db = interaction.client.async_db["Main"].UserNote
        await db.delete_many({
            "Guild": interaction.guild.id
        })
        await interaction.message.edit(embed=discord.Embed(title="ユーザーノートを全消去しました。", color=discord.Color.green()), view=None)

class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ModCog")

    async def SendLog(self, ctx: commands.Context, title: str, 説明: str):
        db = self.bot.async_db["Main"].LoggingChannel
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            await self.bot.get_channel(dbfind["Channel"]).send(embed=discord.Embed(title=f"{title}", description=f"{説明}", color=discord.Color.green()).set_footer(text=f"実行者: {ctx.author.name}"))
        except:
            return
        
    def random_id(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    async def SaveLog(self, ctx: commands.Context, title: str, 説明: str):
        db = self.bot.async_db["Main"].LoggingWeb
        id = self.random_id(10)
        await db.replace_one(
            {"Guild": ctx.guild.id, "ID": id}, 
            {"Guild": ctx.guild.id, "ID": id, "Title": title, "Desc": 説明, "Author": f"{ctx.author.id}/{ctx.author.name}"}, 
            upsert=True
        )

    async def get_mute_role(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].MuteRole
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return ctx.guild.get_role(dbfind["Role"])

    @commands.hybrid_group(name="protect", description="DMを無効化します。", fallback="dm")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def protect_dm(self, ctx: commands.Context, 何日: int, 何時間: int):
        await ctx.defer()
        await ctx.guild.edit(dms_disabled_until=discord.utils.utcnow() + datetime.timedelta(days=float(何日), hours=float(何時間)))
        await ctx.reply(embed=discord.Embed(title="DMを無効化しました。", color=discord.Color.green()))

    @protect_dm.command(name="invite", description="招待を停止します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def protect_invite(self, ctx: commands.Context, 何日: int, 何時間: int):
        await ctx.defer()
        await ctx.guild.edit(dms_disabled_until=discord.utils.utcnow() + datetime.timedelta(days=float(何日), hours=float(何時間)))
        await ctx.reply(embed=discord.Embed(title="招待を無効化しました。", color=discord.Color.green()))

    @commands.hybrid_group(name="note", description="ユーザーノートを設定します。", fallback="set")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def note_set(self, ctx: commands.Context, ユーザー: discord.User, 内容: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].UserNote
        await db.replace_one(
            {"Guild": ctx.guild.id, "User": ユーザー.id}, 
            {"Guild": ctx.guild.id, "User": ユーザー.id, "Content": 内容}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="ノートを設定しました。", color=discord.Color.green(), description=内容))

    @note_set.command(name="show", description="ユーザーノートを表示します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def note_show(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        db = self.bot.async_db["Main"].UserNote
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id, "User": ユーザー.id}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="ユーザーノート", color=discord.Color.green()).add_field(name="ユーザー", value=f"{ユーザー.name} ({ユーザー.id})", inline=False).add_field(name="内容", value="なし"))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="ユーザーノート", color=discord.Color.green()).add_field(name="ユーザー", value=f"{ユーザー.name} ({ユーザー.id})", inline=False).add_field(name="内容", value="なし"))
        await ctx.reply(embed=discord.Embed(title="ユーザーノート", color=discord.Color.green()).add_field(name="ユーザー", value=f"{ユーザー.name} ({ユーザー.id})", inline=False).add_field(name="内容", value=dbfind.get("Content", "なし")))

    @note_set.command(name="remove", description="ユーザーノートを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def note_remove(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        db = self.bot.async_db["Main"].UserNote
        await db.delete_one({
            "User": ユーザー.id,
        })
        await ctx.reply(embed=discord.Embed(title="ユーザーノートを削除しました。", color=discord.Color.green()))

    @note_set.command(name="clear", description="ユーザーノートを全削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def note_clear(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="本当に全消去する？", description="この操作は取り返せません！\n本当に全消去していいの？", color=discord.Color.green()), view=userNoteClear(ctx.author))

    # モデレーション

    @commands.hybrid_group(name="moderation", description="SharkBotでのモデレーションログチャンネルを設定します。", fallback="logging")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def logging_channel(self, ctx: commands.Context, 有効化: bool):
        if 有効化:
            wh_url = await ctx.channel.create_webhook(name="SharkBot-ModLog")
            db = self.bot.async_db["Main"].LoggingChannel
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "WebHook": wh_url.url}, 
                upsert=True
            )
            await self.SendLog(ctx, "ログが有効化されました。", "特に説明はなし")
            await ctx.reply(embed=discord.Embed(title="モデレーションをログを有効化しました。", color=discord.Color.green()))
        else:
            db = self.bot.async_db["Main"].LoggingChannel
            await db.delete_one({
                "Guild": ctx.guild.id,
            })
            await self.SendLog(ctx, "ログが無効化されました。", "特に説明はなし")
            await ctx.reply(embed=discord.Embed(title="モデレーションをログを無効化しました。", color=discord.Color.green()))

    @logging_channel.command(name="lock", description="チャンネルをLockするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_lock(self, ctx: commands.Context, スレッド作成可能か: bool = False, リアクション可能か: bool = False):
        await ctx.defer()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        overwrite.create_polls = False
        overwrite.use_application_commands = False
        overwrite.attach_files = False
        if スレッド作成可能か:
            overwrite.create_public_threads = True
            overwrite.create_private_threads = True
        else:
            overwrite.create_public_threads = False
            overwrite.create_private_threads = False
        if リアクション可能か:
            overwrite.add_reactions = True
        else:
            overwrite.add_reactions = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.SendLog(ctx, "チャンネルがロックされました。", f"ロックされたチャンネル: {ctx.channel.name}")
        await self.SaveLog(ctx, "チャンネルがロックされました。", f"ロックされたチャンネル: {ctx.channel.name}")
        await ctx.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> チャンネルをロックしました。", color=discord.Color.green()))

    @logging_channel.command(name="unlock", description="チャンネルをUnLockするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_unlock(self, ctx: commands.Context):
        await ctx.defer()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        overwrite.create_polls = True
        overwrite.create_public_threads = True
        overwrite.create_private_threads = True
        overwrite.use_application_commands = True
        overwrite.attach_files = True
        overwrite.add_reactions = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.SendLog(ctx, "チャンネルが解放されました。", f"解放されたチャンネル: {ctx.channel.name}")
        await self.SaveLog(ctx, "チャンネルが解放されました。", f"解放されたチャンネル: {ctx.channel.name}")
        await ctx.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> チャンネルを開放しました。", color=discord.Color.green()))

    @logging_channel.command(name="category-copy", description="カテゴリをコピーします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def category_copy(self, ctx: commands.Context, カテゴリ: discord.CategoryChannel):
        await ctx.defer()
        c = await ctx.guild.create_category(name=カテゴリ.name, overwrites=カテゴリ.overwrites)
        for channel in カテゴリ.channels:
            overwrites = channel.overwrites

            if isinstance(channel, discord.TextChannel):
                new_channel = await ctx.guild.create_text_channel(
                    name=channel.name,
                    category=c,
                    topic=channel.topic,
                    slowmode_delay=channel.slowmode_delay,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.VoiceChannel):
                new_channel = await ctx.guild.create_voice_channel(
                    name=channel.name,
                    category=c,
                    bitrate=channel.bitrate,
                    user_limit=channel.user_limit,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.StageChannel):
                new_channel = await ctx.guild.create_stage_channel(
                    name=channel.name,
                    category=c,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.ForumChannel):  # フォーラムチャンネルの場合
                new_channel = await ctx.guild.create_forum_channel(
                    name=channel.name,
                    category=c,
                    topic=channel.topic,
                    overwrites=overwrites
                )
            await asyncio.sleep(2)
        await self.SendLog(ctx, "カテゴリがコピーされました。", f"{カテゴリ.name}")
        await self.SaveLog(ctx, "カテゴリがコピーされました。", f"{カテゴリ.name}")
        await ctx.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> カテゴリをコピーしました。", color=discord.Color.green()), ephemeral=True)

    @logging_channel.command(name="warn", description="メンバーを警告するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_warn(self, ctx: commands.Context, メンバー: discord.Member, 警告文: str):
        await ctx.defer()
        await メンバー.send(embed=discord.Embed(title=f"あなたは`{ctx.guild.name}`で警告されました。", description=警告文, color=discord.Color.yellow()))
        await self.SendLog(ctx, "メンバーを警告しました。", f"警告された人: {メンバー.name}")
        await self.SaveLog(ctx, "メンバーを警告しました。", f"警告された人: {メンバー.name}")
        await ctx.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> メンバーを警告しました。", color=discord.Color.green()))

    @logging_channel.command(name="clear", description="チャンネルをきれいにするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_clear(self, ctx: commands.Context, 数: int):
        if 数 > 100:
            return await ctx.reply("あまりにもメッセージを削除する量が多すぎます！", ephemeral=True)
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            await ctx.channel.purge(limit=数)
            await self.SendLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await self.SaveLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await ctx.send(embed=discord.Embed(title=f"メッセージを削除しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.channel.purge(limit=数 + 1)
            await self.SendLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await self.SaveLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await ctx.channel.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> メッセージを削除しました。", color=discord.Color.green()))

    @logging_channel.command(name="now-down-clear", description="特定のメッセージより下のメッセージを指定個数削除するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def now_down_mod_clear(self, ctx: commands.Context, メッセージ: discord.Message, 数: int):
        if 数 > 100:
            return await ctx.reply("あまりにもメッセージを削除する量が多すぎます！", ephemeral=True)
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            await ctx.channel.purge(limit=数, after=メッセージ)
            await ctx.send(embed=discord.Embed(title=f"メッセージを削除しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.channel.purge(limit=数 + 1, after=メッセージ)
            await ctx.channel.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> メッセージを削除しました。", color=discord.Color.green()))

    @logging_channel.command(name="now-on-clear", description="特定のメッセージより上のメッセージを指定個数削除するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def now_on_mod_clear(self, ctx: commands.Context, メッセージ: discord.Message, 数: int):
        if 数 > 100:
            return await ctx.reply("あまりにもメッセージを削除する量が多すぎます！", ephemeral=True)
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            await ctx.channel.purge(limit=数, before=メッセージ)
            await ctx.send(embed=discord.Embed(title=f"メッセージを削除しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.channel.purge(limit=数 + 1, after=メッセージ)
            await ctx.channel.send(embed=discord.Embed(title=f"<:Success:1362271281302601749> メッセージを削除しました。", color=discord.Color.green()))

    @logging_channel.command(name="remake", description="チャンネルを再生成するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_remake(self, ctx: commands.Context):
        await ctx.defer()
        ch = await ctx.channel.clone()
        await ch.edit(position=ctx.channel.position+1)
        await ctx.channel.delete()
        await asyncio.sleep(1)
        await ch.send("<:Success:1362271281302601749> 再生成しました。")

    @logging_channel.command(name="timeout", description="ユーザーをタイムアウトします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_mute(self, ctx: commands.Context, メンバー: discord.Member, 分: int):
        user_id = ctx.author.id
        class CheckButton(discord.ui.View):
            def __init__(self, ctx, bot, member: discord.Member, tid: int):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.member = member
                self.tid = tid
                self.bots = bot
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                try:
                    timeout_duration = datetime.timedelta(minutes=self.tid)
                    await self.member.timeout(timeout_duration)
                    await self.bots.SendLog(ctx, "メンバーがタイムアウトされました。", f"Muteされた人: {メンバー.name}")
                    await self.bots.SaveLog(ctx, "メンバーがタイムアウトされました。", f"Muteされた人: {メンバー.name}")
                    await interaction.message.edit(content=None, embed=discord.Embed(title=f"{メンバー.display_name}をMuteしました。", color=discord.Color.green()), view=None)
                except:
                    await interaction.message.edit(content=None, embed=discord.Embed(title=f"Muteに失敗しました。", color=discord.Color.green()), view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)

        await ctx.reply(embed=discord.Embed(title=f"{メンバー.display_name}\nをMuteしていいですか？", color=discord.Color.yellow()), view=CheckButton(ctx, bot=self, member=メンバー, tid=分))

    @logging_channel.command(name="remove-timeout", description="ユーザーのタイムアウトを解除するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_unmute(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
        await メンバー.edit(timed_out_until=None)
        await self.SendLog(ctx, "タイムアウトを解除しました。", f"UnMuteされた人: {メンバー.name}")
        await self.SaveLog(ctx, "タイムアウトを解除しました。", f"UnMuteされた人: {メンバー.name}")
        await ctx.send(embed=discord.Embed(title=f"{メンバー.display_name}のタイムアウトを解除しました。", color=discord.Color.green()))

    @logging_channel.command(name="multi-ban", description="複数メンバーを一気にBANします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def multi_ban(self, ctx: commands.Context, キーワード: str, 理由: str):
        await ctx.defer()
        guild = ctx.guild
        members_to_ban = [member for member in guild.members if キーワード.lower() in member.display_name.lower()]

        if not members_to_ban:
            await ctx.send(f"メンバーが見つかりませんでした。")
            return

        for member in members_to_ban:
            if member.id == 1322100616369147924:
                continue
            try:
                await member.ban(reason=理由)
            except discord.Forbidden:
                continue
            await asyncio.sleep(2)
        await self.SendLog(ctx, "複数メンバーがBANされました。", f"理由: {理由}")
        await self.SaveLog(ctx, "複数メンバーがBANされました。", f"理由: {理由}")
        await ctx.reply(embed=discord.Embed(title="複数メンバーをBANしました。", description=f"{len(members_to_ban)}人", color=discord.Color.green()))

    @logging_channel.command(name="ban", description="ユーザーをBANします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, ユーザー: discord.User, 理由: str):
        user_id = ctx.author.id
        class CheckButton(discord.ui.View):
            def __init__(self, ctx, bot, member: discord.User, 理由: str):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.member = member
                self.reas = 理由
                self.bots = bot
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                await ctx.guild.ban(self.member, reason=self.reas)
                await self.bots.SendLog(ctx, "メンバーがBANされました。", f"BANされた人: {self.member.name}\n理由: {self.reas}")
                await self.bots.SaveLog(ctx, "メンバーがBANされました。", f"BANされた人: {self.member.name}\n理由: {self.reas}")
                await interaction.message.edit(content=None, embed=discord.Embed(title=f"{self.member.display_name}をBANしました。", color=discord.Color.green()), view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not user_id == interaction.user.id:
                    return
                await interaction.response.defer()
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}\nをBANしていいですか？", color=discord.Color.yellow()), view=CheckButton(ctx, self, ユーザー, 理由))

    @logging_channel.command(name="unban", description="ユーザーをUnBANします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx: commands.Context, ユーザー: discord.User, 理由: str = None):
        await ctx.defer()
        await ctx.guild.unban(ユーザー, reason=理由)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.name}をUnBanしました。", color=discord.Color.green()))

    @logging_channel.command(name="kick", description="ユーザーをKICKします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx: commands.Context, ユーザー: discord.User, 理由: str):
        if ユーザー.id == ctx.author.id:
            return await ctx.reply(embed=discord.Embed(title=f"自分自身はキックできません。", color=discord.Color.red()))
        await ctx.guild.kick(ユーザー, reason=理由)
        await ctx.reply(embed=discord.Embed(title=f"<:Success:1362271281302601749> {ユーザー.name}をKickしました。", color=discord.Color.red()))
        await self.SendLog(ctx, "メンバーがKickされました。", f"Kickされた人: {ユーザー.name}\n理由: {理由}")
        await self.SaveLog(ctx, "メンバーがKickされました。", f"Kickされた人: {ユーザー.name}\n理由: {理由}")

    @logging_channel.command(name="serverban", description="web認証時に特定のサーバーに参加してる場合に、認証できなくします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def server_ban(self, ctx: commands.Context, サーバーid: str, 理由: str):
        db = self.bot.async_db["Main"].GuildBAN
        await db.replace_one(
            {"Guild": str(ctx.guild.id), "BANGuild": サーバーid}, 
            {"Guild": str(ctx.guild.id), "BANGuild": サーバーid}, 
            upsert=True
        )
        await self.SendLog(ctx, "サーバーをBANしました。", f"理由: {理由}")
        await self.SaveLog(ctx, "サーバーをBANしました。", f"理由: {理由}")
        return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> サーバーをBANしました。", color=discord.Color.green()))

    @logging_channel.command(name="serverunban", description="IPアドレスのユーザーのBANを解除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def server_unban(self, ctx: commands.Context, サーバーid: str, 理由: str):
        db = self.bot.async_db["Main"].GuildBAN
        await db.delete_one(
            {"Guild": str(ctx.guild.id), "BANGuild": サーバーid}
        )
        await self.SendLog(ctx, "サーバーをUnBANしました。", f"理由: {理由}")
        await self.SaveLog(ctx, "サーバーをUnBANしました。", f"理由: {理由}")
        return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> サーバーをunBANしました。", color=discord.Color.green()))

    def rot_n(self, s: str, n: int) -> str:
        answer = ''
        for letter in s:
            if 'a' <= letter <= 'z':  # 小文字の範囲
                answer += chr(ord('a') + (ord(letter) - ord('a') + n) % 26)
            elif 'A' <= letter <= 'Z':  # 大文字の範囲
                answer += chr(ord('A') + (ord(letter) - ord('A') + n) % 26)
            else:
                answer += letter  # それ以外の文字はそのまま
        return answer

    @logging_channel.command(name="top-member", description="特定のメンバーをメンバーリストのトップにします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_nicknames=True)
    async def top_member(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
        if メンバー.guild_permissions.administrator:
            return await ctx.reply(embed=discord.Embed(title="そのメンバーは管理者権限が\n付いているため使用できません。", color=discord.Color.red()))
        await メンバー.edit(nick=f"!{メンバー.display_name}")
        await self.SendLog(ctx, title=f"メンバーの位置が調整されました。", 説明=f"メンバー: {メンバー.mention}")
        await self.SaveLog(ctx, title=f"メンバーの位置が調整されました。", 説明=f"メンバー: {メンバー.mention}")
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> メンバーをトップにしました。", color=discord.Color.green(), description=f"{メンバー.name}"))

    @logging_channel.command(name="name-sort", description="メンバーを指定した順に並び替えます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_nicknames=True)
    async def name_sort(self, ctx: commands.Context, メンバー_スペースで区切る: str):
        await ctx.defer()
        co = 0
        mls = メンバー_スペースで区切る.split(" ")
        m_l = []
        for m in mls:
            mm = ctx.guild.get_member(int(m))
            co += 1
            try:
                await mm.edit(nick=None)
                await asyncio.sleep(0.7)
                if co == 1:
                    await mm.edit(nick=f"!_{mm.display_name}")
                elif co == 2:
                    await mm.edit(nick=f"#_{mm.display_name}")
                elif co == 3:
                    await mm.edit(nick=f"(_{mm.display_name}")
                elif co == 4:
                    await mm.edit(nick=f"._{mm.display_name}")
                else:
                    await mm.edit(nick=f"{co - 4}_{mm.display_name}")
            except:
                continue
            m_l.append(f"{co}.{mm.name}")
            await asyncio.sleep(2)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 好きな順に並び替えました。", color=discord.Color.green(), description="\n".join(m_l)))

    @logging_channel.command(name="invite-cleaner", description="特定の人、または特定の人以外の招待リンクを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def invite_cleaner(self, ctx: commands.Context, 削除しないユーザー: discord.User = None, 削除するユーザー: discord.User = None):
        await ctx.defer()
        if 削除しないユーザー:
            invites = await ctx.guild.invites()
            for inv in invites:
                if not 削除しないユーザー == inv.inviter:
                    await inv.delete()
                    await asyncio.sleep(1)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 招待リンクを整理しました。", color=discord.Color.green()))
            return
        if 削除するユーザー:
            invites = await ctx.guild.invites()
            for inv in invites:
                if 削除するユーザー == inv.inviter:
                    await inv.delete()
                    await asyncio.sleep(1)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 招待リンクを整理しました。", color=discord.Color.green()))
            return
        await self.SendLog(ctx, title=f"招待リンクが整理されました。", 説明=f"特になし")
        await self.SaveLog(ctx, title=f"招待リンクが整理されました。", 説明=f"特になし")
        await ctx.reply(embed=discord.Embed(title="どちらかを指定してください。", color=discord.Color.red(), description="削除しないユーザーか削除するユーザー、\nどっちかを指定してください。\n二つ同時に指定することはできません。"))

    async def add_reactions_from_text(self, message, text):
        kakasi = pykakasi.kakasi()
        result = kakasi.convert(text)
        
        error_moji = 0

        def text_to_discord_emoji(text):
            emoji_map = {chr(97 + i): chr(0x1F1E6 + i) for i in range(26)}
            num_emoji_map = {str(i): f"{i}️⃣" for i in range(10)}
            return [emoji_map[char.lower()] if char.isalpha() else num_emoji_map[char] if char.isdigit() else None for char in text if char.isalnum()]
        
        romaji_text = "".join(item["kunrei"] for item in result if "kunrei" in item)
        emojis = text_to_discord_emoji(romaji_text)
        
        for e in emojis:
            if e:
                try:
                    await message.add_reaction(e)
                    await asyncio.sleep(1)
                except Exception as err:
                    error_moji += 1
                    continue
        return error_moji

    @logging_channel.command(name="emoji-art", description="テキストをリアクションにします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def emoji_art(self, ctx: commands.Context, テキスト: str, メッセージid: discord.Message):
        await ctx.defer(ephemeral=True)
        await self.add_reactions_from_text(メッセージid, テキスト)
        await ctx.reply(ephemeral=True, embed=discord.Embed(title="<:Success:1362271281302601749> アートを作成しました。", color=discord.Color.green()))

    @logging_channel.command(name="report", description="ユーザーやサーバーを通報をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def report_command(self, ctx: commands.Context, ユーザー: discord.User = None, 理由: str = "理由なし"):
        await ctx.defer(ephemeral=True)
        if not ユーザー:
            type_ = "サーバー"
        else:
            if ユーザー.id == 1335428061541437531:
                return await ctx.reply(ephemeral=True, embed=discord.Embed(title="通報が完了しました。", description="ありがとうございます。", color=discord.Color.green()))
            elif ユーザー.id == 1322100616369147924:
                return await ctx.reply(ephemeral=True, embed=discord.Embed(title="通報が完了しました。", description="ありがとうございます。", color=discord.Color.green()))
            type_ = "ユーザー"
        if type_ == "サーバー":
            target = ctx.guild
        else:
            target = ユーザー
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="BotからBAN", custom_id="botban+", style=discord.ButtonStyle.red))
        view.add_item(discord.ui.Button(label="警告", custom_id="botwarn+", style=discord.ButtonStyle.blurple))
        view.add_item(discord.ui.Button(label="破棄", custom_id="botdelete+"))
        await self.bot.get_channel(1352489257297510411).send(view=view, embed=discord.Embed(title=f"{ctx.author.name}さんからの通報", color=discord.Color.yellow()).add_field(name="タイプ", value=f"{type_}", inline=False).add_field(name=f"{type_}", value=f"{target.name} ({target.id})", inline=False).add_field(name=f"理由", value=理由, inline=False).set_footer(text=f"{target.id}"))
        await ctx.reply(ephemeral=True, embed=discord.Embed(title="<:Success:1362271281302601749> 通報が完了しました。", description="ありがとうございます。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(ModCog(bot))