from discord.ext import commands, ipc, oauth2
import discord
import time
import traceback
import sys
from discord import Webhook
import aiofiles
import aiohttp
import json
import io
import logging
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageChops
import datetime
import aiohttp
import traceback
import textwrap
import random
from functools import partial
import string

COOLDOWN_TIME_BOTJOIN = 60
cooldown_bot_join = {}

join_times = {}

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.tko = self.tkj["Token"]
            self.tkob = self.tkj["BetaToken"]
        print(f"init -> AdminCog")

    @commands.command(name="exit", hidden=True)
    @commands.is_owner()
    async def exit_bot_admin(self, ctx):
        await ctx.reply("Botをシャットダウンしています。。")
        await self.bot.close()
        sys.exit()

    @commands.command(name="reload", aliases=["re", "rel"], hidden=True, description="CogをReloadします。(オーナー専用)")
    async def reload_admin(self, ctx: commands.Context, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await self.bot.tree.sync()
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")

    @commands.command(name="sync_slash", aliases=["sy"], hidden=True, description="スラッシュコマンドを同期します。 (オーナー専用)")
    async def sync_slash(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await self.bot.tree.sync()
            await ctx.reply("スラッシュコマンドを同期しました。")

    @commands.command(name="reload_", hidden=True, description="CogをSyncせずにReloadします。(オーナー専用)")
    @commands.is_owner()
    async def reload_admin_two(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")

    @commands.command(name="visit", hidden=True, description="サーバーのチャンネルにアクセスします。")
    @commands.is_owner()
    async def visit_guild(self, ctx, channel: int):
        if ctx.author.id == 1335428061541437531:
            ms = io.StringIO("\n".join([f"{message.content} {message.author.name}/{message.author.id}" async for message in self.bot.get_channel(channel).history(limit=150)]))
            await ctx.reply(file=discord.File(ms, "visit.txt"))

    @commands.command(name="load", hidden=True, description="CogをLoadします。(オーナー専用)")
    @commands.is_owner()
    async def load_admin(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.load_extension(f"cogs.{cogname}")
            await ctx.reply(f"LoadOK .. `cogs.{cogname}`")

    @commands.command(name="database", hidden=True)
    async def database(self, ctx, *, command: str):
        if not ctx.author.id == 1335428061541437531:
            return
        db = self.bot.async_db["Main"]
        cmd = ""
        for c in command.split("\n"):
            cmd += f"{await db.command(c)}"
        await ctx.reply(f"{cmd[:2000]}")

    @commands.command(name="ban_user", hidden=True)
    async def banuser(self, ctx, user: discord.User):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.replace_one(
                {"User": user.id}, 
                {"User": user.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{user.name}をBotからBANしました。", color=discord.Color.red()))

    @commands.command(name="unban_user", hidden=True)
    async def unban_user(self, ctx, user: discord.User):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.delete_one({
                "User": user.id
            })
            await ctx.reply(embed=discord.Embed(title=f"{user.name}のBotからのBANを解除しました。", color=discord.Color.red()))

    @commands.command(name="ban_guild", hidden=True)
    async def ban_guild(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].BlockGuild
            await db.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}をBotからBANしました。", color=discord.Color.red()))

    @commands.command(name="unban_guild", hidden=True)
    async def unban_guild(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].BlockGuild
            await db.delete_one({
                "Guild": guild.id
            })
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}のBotからのBANを解除しました。", color=discord.Color.red()))

    async def send_one_globalchat_ann(self, webhook: str, メッセージ: str):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=メッセージ, color=discord.Color.blue())
            embed.set_footer(text=f"Sharkbot")

            embed.set_author(name=f"SharkBot/{self.bot.user.id}", icon_url=self.bot.user.avatar.url)
            await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")

    @commands.command(name="send_gc", hidden=True)
    async def send_gc(self, ctx, *, メッセージ: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].NewGlobalChat
            channels = db.find({})

            tasks = []
            async for channel in channels:
                target_channel = self.bot.get_channel(channel["Channel"])
                if target_channel:
                    tasks.append(self.send_one_globalchat_ann(channel["Webhook"], メッセージ))
                else:
                    print(f"{channel['Channel']} が見つからないため削除します。")
                    await db.delete_one({"Channel": channel["Channel"]})

            if tasks:
                await asyncio.gather(*tasks)
            await ctx.reply(embed=discord.Embed(title=f"グローバルチャットに送信しました。", color=discord.Color.green()))

    @commands.command(name="make_error", hidden=True)
    @commands.is_owner()
    async def make_error_admin(self, ctx, errorname: str):
        raise Exception(errorname)
    
    @commands.command(name="add_mod", hidden=True, description="モデレーターを追加します。 (オーナー専用)")
    async def add_mod(self, ctx, ユーザー: discord.User):
        if ctx.author.id == 1335428061541437531:
            if not self.bot.get_guild(1343124570131009579).get_member(ユーザー.id):
                return await ctx.reply("条件を満たしていないため追加できません。。\nサポートサーバーにいる必要があります。")
            role = self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            await self.bot.get_guild(1343124570131009579).get_member(ユーザー.id).add_roles(role)
            return await ctx.reply("モデレーターを追加しました。")
        
    @commands.command(name="remove_mod", hidden=True, description="モデレーターを剥奪します。 (オーナー専用)")
    async def remove_mod(self, ctx, ユーザー: discord.User):
        if ctx.author.id == 1335428061541437531:
            if not self.bot.get_guild(1343124570131009579).get_member(ユーザー.id):
                return await ctx.reply("条件を満たしていないため剥奪できません。。\nサポートサーバーにいる必要があります。")
            role = self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            await self.bot.get_guild(1343124570131009579).get_member(ユーザー.id).remove_roles(role)
            return await ctx.reply("モデレーターを剥奪しました。")

    @commands.command(name="guilds_list", hidden=True, description="サーバーのリストを取得します。(管理人専用)")
    async def guilds_list(self, ctx):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            text = ""
            for g in self.bot.guilds:
                text += f"{g.name} - {g.id}\n"
            slist = text.split("\n")
            b = 0
            n = 30
            msg = await ctx.reply(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
            await msg.add_reaction("<:left:1361911044250796042>")
            await msg.add_reaction("<:right:1361911055583809546>")
            await msg.add_reaction("<:cancel:1361911249046208684>")
            try:
                while True:
                    r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=None)
                    await r.remove(ctx.author)
                    if r.emoji.id == 1361911044250796042:
                        b -= 30
                        n -= 30
                        await msg.edit(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
                    elif r.emoji.id == 1361911055583809546:
                        b += 30
                        n += 30
                        await msg.edit(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
                    else:
                        await msg.edit(embed=None, content="閉じました。")
                        return
            except:
                return
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="guild_channels", hidden=True)
    async def guild_channels_info(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}のチャンネル", description="\n".join([f"{g.name} - {g.id}" for g in guild.channels]), color=discord.Color.green()))
        else:
            return

    @commands.command(name="leave_guild", aliases=["lg"], hidden=True, description="サーバーから退出します。(オーナー専用)")
    async def leave_guild(self, ctx, guild: discord.Guild):
        if ctx.author.id == 1335428061541437531:
            await guild.leave()
            await ctx.reply(f"{guild.name}から退出しました。")

    @commands.command(name="get_invite", hidden=True, description="サーバーの招待リンクを取得します。(管理者専用)")
    async def get_invite(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            for i in guild.channels:
                try:
                    inv = await i.create_invite()
                    await ctx.reply(f"{inv.url}")
                    return
                except:
                    continue

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, text: str):
        ev = eval(text)
        await ctx.reply(ev)

    @commands.command(name="mongodb_select", hidden=True)
    @commands.is_owner()
    async def mongodb_select(self, ctx, db: str, filter1: str, intb: bool, *, filter2: str):
        try:
            mdb = self.bot.async_db["Main"][db]
        except:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        try:
            if intb:
                dbfind = await mdb.find_one({filter1: int(filter2)}, {"_id": False})
            else:
                dbfind = await mdb.find_one({filter1: filter2}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"```{dbfind}```", color=discord.Color.green()))

    """
    @commands.command(name="allclear_test", hidden=True)
    @commands.is_owner()
    async def allclear_test(self, ctx: commands.Context):
        ch = await ctx.channel.clone()
        await ch.edit(position=ctx.channel.position+1)
        await ctx.channel.delete()
    """

    # ユーザーの処罰

    """
    @commands.command(name="gmute", hidden=True, description="ユーザーをグローバルチャットでMuteします。(管理人専用)")
    async def gmute(self, ctx: commands.Context, ユーザー: discord.User, *, 理由: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            msg = await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}をGMuteしますか？", description=f"ID: {ユーザー.id}\nUserName: {ユーザー.name}\nDisplayName: {ユーザー.display_name}", color=discord.Color.red()))
            await msg.add_reaction("<:Check:1346687320404922418>")
            await msg.add_reaction("<:Cancel:1346686859757224057>")
            try:
                r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                if r.emoji.id == 1346687320404922418:
                    db = self.bot.async_db["Main"].GMute
                    await db.replace_one(
                        {"User": ユーザー.id}, 
                        {"User": ユーザー.id, "Reason": 理由}, 
                        upsert=True
                    )
                    await ctx.channel.send(embed=discord.Embed(title="GMuteしました。", color=discord.Color.red()))
                else:
                    await ctx.channel.send(embed=discord.Embed(title="キャンセルしました。", color=discord.Color.red()))
            except TimeoutError:
                await ctx.channel.send(embed=discord.Embed(title="タイムアウトしました。", color=discord.Color.red()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="ungmute", hidden=True, description="ユーザーをグローバルチャットでUnMuteします。(管理人専用)")
    async def ungmute(self, ctx: commands.Context, ユーザー: discord.User, *, 理由: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            msg = await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}をUnGMuteしますか？", description=f"ID: {ユーザー.id}\nUserName: {ユーザー.name}\nDisplayName: {ユーザー.display_name}", color=discord.Color.red()))
            await msg.add_reaction("<:Check:1346687320404922418>")
            await msg.add_reaction("<:Cancel:1346686859757224057>")
            try:
                r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                if r.emoji.id == 1346687320404922418:
                    db = self.bot.async_db["Main"].GMute
                    result = await db.delete_one({
                        "User": ユーザー.id,
                    })
                    await ctx.channel.send(embed=discord.Embed(title="UnGMuteしました。", color=discord.Color.red()))
                else:
                    await ctx.channel.send(embed=discord.Embed(title="キャンセルしました。", color=discord.Color.red()))
            except TimeoutError:
                await ctx.channel.send(embed=discord.Embed(title="タイムアウトしました。", color=discord.Color.red()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    """

    @commands.command(name="check_autoban", hidden=True)
    @commands.is_owner()
    async def check_autoban(self, ctx):
        gs = []
        db = self.bot.async_db["Main"].AutoBAN
        async for gd in db.find():
            gs.append(f"{self.bot.get_guild(gd["Guild"]).name} {gd["Guild"]}")
        return await ctx.reply(f"```{"\n".join(gs)}```")
    
    @commands.command(name="check_test", hidden=True)
    @commands.is_owner()
    async def check_test(self, ctx: commands.Context):
        class CheckButton(discord.ui.View):
            def __init__(self, ctx):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await interaction.message.edit(content="承認されました。", embed=None, view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)
        await ctx.reply(embed=discord.Embed(title="チェックしています。", color=discord.Color.yellow()), view=CheckButton(ctx))

    @commands.command(name="get_args", hidden=True)
    @commands.is_owner()
    async def get_args(self, ctx, *, command_name: str):
        command = self.bot.get_command(command_name)
        if not command:
            await ctx.send(f"コマンド `{command_name}` は存在しません。")
            return

        params = command.clean_params
        if not params:
            await ctx.send(f"コマンド `{command_name}` には引数がありません。")
        else:
            args_info = [f"{name}: {param.annotation}" for name, param in params.items()]
            args_text = "\n".join(args_info)
            await ctx.send(f"コマンド `{command_name}` の引数:\n{args_text}")

    @commands.command(name="test_guilds", hidden=True)
    @commands.is_owner()
    async def test_guilds(self, ctx: commands.Context):
        th = self.bot.get_channel(1330146277601574912).threads
        ths = [f"{i.name}" for i in th]
        await ctx.reply(embed=discord.Embed(title="連携サーバー", description="\n".join(ths), color=discord.Color.green()))

    async def fetch_avatar(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.read()

    @commands.command("takmute", description="？？？(管理人専用)")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def takmute(self, ctx):
        if not ctx.author.id == 1335428061541437531:
            return
        
        reas = ""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.takasumibot.com/v1/mute_user") as q:
                js = await q.json()
                for j in js["data"]:
                    reas += f"{j.get("id")} ({j.get("reason")})\n"

        io_ = io.StringIO(reas)
        
        await ctx.reply(file=discord.File(io_, "tak.txt"))

        io_.close()

    @commands.command("active_level_test", description="？？？(管理人専用)")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def active_level_test(self, ctx, msg: discord.Message):
        if not ctx.author.id == 1335428061541437531:
            return
        
        if not msg.embeds:
            return
        
        embed = msg.embeds[0].fields[0].value.split("_**ActiveLevel ... ")[1].replace("**_", "")
        await ctx.reply(f"{embed}")

    @commands.command("save", description="セーブデータをセーブします。(管理人専用)")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def save(self, ctx):
        if not ctx.author.id == 1335428061541437531:
            return

        def is_owner_check(check):
            return getattr(check, "__qualname__", "").startswith("is_owner")

        commands_data = []

        db = self.bot.async_db["Main"].CommandsList

        for command in self.bot.commands:
            # Botオーナー専用・管理者専用のコマンドは保存しない
            if any(is_owner_check(check) for check in command.checks):
                continue

            command_data = {
                "name": command.name,
                "description": command.description or "説明なし",
                "type": "command",
                "is_hybrid": isinstance(command, commands.HybridCommand),
                "subcommands": [],
            }

            if isinstance(command, commands.HybridGroup) or isinstance(command, commands.Group):
                command_data["type"] = "group" if isinstance(command, commands.Group) else "hybrid_group"

                # サブコマンドの追加
                for subcommand in command.commands:
                    if any(is_owner_check(check) for check in subcommand.checks):
                        continue  # Botオーナー専用・管理者専用のサブコマンドは除外

                    command_data["subcommands"].append({
                        "name": subcommand.name,
                        "description": subcommand.description or "説明なし",
                        "is_hybrid": isinstance(subcommand, commands.HybridCommand),
                    })

                # HybridGroup の Fallback コマンドを取得
                if isinstance(command, commands.HybridGroup):
                    fallback = getattr(command, "_fallback_command", None)
                    if fallback:
                        command_data["fallback"] = {
                            "name": fallback.name,
                            "description": fallback.description or "説明なし",
                            "is_hybrid": isinstance(fallback, commands.HybridCommand),
                        }

            commands_data.append(command_data)

        # MongoDBへ保存
        db.delete_many({})
        db.insert_many(commands_data)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://discordpy.readthedocs.io/ja/latest/api.html") as response:
                async with aiofiles.open("Document/discord-py.html", mode='w', encoding="utf-8") as f:
                    await f.write(await response.text())

        await ctx.reply("セーブ完了！")

    @commands.command(name="sync_guilds")
    @commands.is_owner()
    async def sync_guilds(self, ctx: commands.Context):
        db_ = self.bot.async_db["Dashboard"].DashboardGuilds
        for g in self.bot.guilds:
            try:
                owner_id = g.owner_id
                guild_icon = g.icon.url if g.icon else "https://www.sharkbot.xyz/static/server.png"
                
                await db_.replace_one(
                    {"Guild": g.id},
                    {"Guild": g.id, "Owner": owner_id, "GuildName": g.name, "GuildIcon": guild_icon},
                    upsert=True
                )
            except Exception as e:
                continue
        await ctx.message.add_reaction("✅")

    @commands.Cog.listener("on_guild_update")
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        try:
            db = self.bot.async_db["Dashboard"].DashboardGuilds
            guild_icon = after.icon.url if after.icon else "https://www.sharkbot.xyz/static/server.png"
            await db.replace_one(
                {"Guild": after.id}, 
                {"Guild": after.id, "Owner": after.owner_id, "GuildName": after.name, "GuildIcon": guild_icon}, 
                upsert=True
            )
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_dashboard(self, guild: discord.Guild):
        try:
            db = self.bot.async_db["Dashboard"].DashboardGuilds
            guild_icon = guild.icon.url if guild.icon else "https://www.sharkbot.xyz/static/server.png"
            await db.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id, "Owner": guild.owner_id, "GuildName": guild.name, "GuildIcon": guild_icon}, 
                upsert=True
            )
        except:
            return


    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_dashboard(self, guild: discord.Guild):
        db = self.bot.async_db["Dashboard"].DashboardGuilds
        await db.delete_one({
            "Guild": guild.id,
        })

    async def auto_setting_enable(self, guild: discord.Guild):
        try:
            await self.bot.async_db["Main"].ExpandSettings.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id}, 
                upsert=True
            )
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_message(self, guild: discord.Guild):
        try:
            for ch in guild.channels:
                await self.auto_setting_enable(guild)
                try:
                    await ch.send(embed=discord.Embed(title="やっほ～！SharkBotだよ～！", description="""導入ありがとう！
このBotには、
認証機能やロールパネル、グローバルチャットがあるよ！
また、AutoModや経済機能、面白い機能もあるよ！
よろしくね！
""", color=discord.Color.blue()), view=discord.ui.View().add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk")))
                except:
                    return
                return
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
        db = self.bot.async_db["Main"].BlockUser
        try:
            profile = await db.find_one({"User": guild.owner.id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                return
        except:
            return

    @commands.command(name="point_add", hidden=True)
    async def point_add(self, ctx: commands.Context, user: discord.User, point: int):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].SharkBotInstallPoint
            user_data = await db.find_one({"_id": user.id})
            if user_data:
                await db.update_one({"_id": user.id}, {"$inc": {"count": point}})
            else:
                await db.insert_one({"_id": user.id, "count": point})
            await ctx.message.add_reaction("✅")
        else:
            return

    async def send_raw_interaction(self, channel: int):
        url = f"https://discord.com/api/v10/channels/{channel}/messages"
        headers = {
            "Authorization": f"Bot {self.bot.http.token}",
            "Content-Type": "application/json"
        }
        data = {
            "flags": 32768,
            "components": [
                {
                "type": 17,
                "components": [
                    {
                    "type": 10,
                    "content": "これはテストです！"
                    },
                    {
                    "type": 9,
                    "components": [
                        {
                        "type": 10,
                        "content": "A list of all the components:"
                        }
                    ],
                    "accessory": {
                        "type": 2,
                        "style": 5,
                        "label": "Reference",
                        "url": "https://discord.com/developers/docs/components/reference#what-is-a-component-component-types"
                    }
                    },
                ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.text()
        
    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_point(self, guild: discord.Guild):
        return
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": guild.owner_id})
        if user_data:
            await db.update_one({"_id": guild.owner_id}, {"$inc": {"count": 5}})
        else:
            await db.insert_one({"_id": guild.owner_id, "count": 5})

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(embed=discord.Embed(title=f"{guild.name}に参加しました。", description=f"{guild.id}", color=discord.Color.green()))
                
    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(embed=discord.Embed(title=f"{guild.name}から退出しました。", color=discord.Color.red()))

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        return
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://discord.com/api/webhooks/1344584369641095221/TK3RKD2mhp-qj8EC39kkplu3r6yTXAkL1IYlh9ck1eNWwrm0QFXeSmkTlMqRUl4jn2Ri', data ={"content": f"{ctx.author.id}/{ctx.author.name}がコマンドを実行しました。\nサーバー: {ctx.guild.id}/{ctx.guild.name}\nコマンド名: {ctx.command.name}"}) as response:
                return

    PERMISSION_TRANSLATIONS = {
            "administrator": "管理者",
            "view_audit_log": "監査ログの表示",
            "view_guild_insights": "サーバーインサイトの表示",
            "manage_guild": "サーバーの管理",
            "manage_roles": "ロールの管理",
            "manage_channels": "チャンネルの管理",
            "kick_members": "メンバーのキック",
            "ban_members": "メンバーのBAN",
            "create_instant_invite": "招待の作成",
            "change_nickname": "ニックネームの変更",
            "manage_nicknames": "ニックネームの管理",
            "manage_emojis_and_stickers": "絵文字とステッカーの管理",
            "manage_webhooks": "Webhookの管理",
            "view_channel": "チャンネルの閲覧",
            "send_messages": "メッセージの送信",
            "send_tts_messages": "TTSメッセージの送信",
            "manage_messages": "メッセージの管理",
            "embed_links": "埋め込みリンクの送信",
            "attach_files": "ファイルの添付",
            "read_message_history": "メッセージ履歴の閲覧",
            "read_messages": "メッセージの閲覧",
            "external_emojis": "絵文字を管理",
            "mention_everyone": "everyone のメンション",
            "use_external_emojis": "外部絵文字の使用",
            "use_external_stickers": "外部ステッカーの使用",
            "add_reactions": "リアクションの追加",
            "connect": "ボイスチャンネルへの接続",
            "speak": "発言",
            "stream": "配信",
            "mute_members": "メンバーのミュート",
            "deafen_members": "メンバーのスピーカーミュート",
            "move_members": "ボイスチャンネルの移動",
            "use_vad": "音声検出の使用",
            "priority_speaker": "優先スピーカー",
            "request_to_speak": "発言リクエスト",
            "manage_events": "イベントの管理",
            "use_application_commands": "アプリケーションコマンドの使用",
            "manage_threads": "スレッドの管理",
            "create_public_threads": "公開スレッドの作成",
            "create_private_threads": "非公開スレッドの作成",
            "send_messages_in_threads": "スレッド内でのメッセージ送信",
            "use_embedded_activities": "アクティビティの使用",
            "moderate_members": "メンバーのタイムアウト",
            "use_soundboard": "サウンドボードの使用",
            "manage_expressions": "絵文字などの管理",
            "create_events": "イベントの作成",
            "create_expressions": "絵文字などの作成",
            "use_external_sounds": "外部のサウンドボードなどの使用",
            "use_external_apps": "外部アプリケーションの使用",
            "view_creator_monetization_analytics": "ロールサブスクリプションの分析情報を表示",
            "send_voice_messages": "ボイスメッセージの送信",
            "send_polls": "投票の作成",
            "external_stickers": "外部のスタンプの使用",
            "use_voice_activation": "ボイスチャンネルでの音声検出の使用"
    }

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        error_details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a
        elif isinstance(error, commands.MissingRequiredArgument):
            params = ctx.command.clean_params
            response = []
            for name, param in params.items():
                param_type = param.annotation
                if param_type == str:
                    msg = f"文字列:{name}"
                elif param_type == int:
                    msg = f"数字:{name}"
                elif param_type == bool:
                    msg = f"オンオフ:{name}"
                elif param_type == discord.User:
                    msg = f"ユーザー:{name}"
                elif param_type == discord.Member:
                    msg = f"メンバー:{name}"
                elif param_type == discord.Guild:
                    msg = f"サーバー:{name}"
                elif param_type == discord.Role:
                    msg = f"ロール:{name}"
                elif param_type == discord.TextChannel:
                    msg = f"テキストチャンネル:{name}"
                elif param_type == discord.VoiceChannel:
                    msg = f"VC:{name}"
                elif param_type == discord.CategoryChannel:
                    msg = f"カテゴリチャンネル:{name}"
                elif param_type == discord.Message:
                    msg = f"メッセージ:{name}"
                else:
                    msg = f"不明:{name}"
                response.append(msg)
            args_text = " ".join(response)
            await ctx.send(embed=discord.Embed(title="<:Error:1362271424227709028> 引数が不足しています。", description=f"```コマンド名 {args_text}```", color=discord.Color.red()))
        elif isinstance(error, commands.NotOwner):
            a = None
            return a
        elif isinstance(error, commands.NSFWChannelRequired):
            return await ctx.send(embed=discord.Embed(title="<:Error:1362271424227709028> NSFWチャンネル専用です。", description=f"うん。", color=discord.Color.red()), ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            missing_perms = [self.PERMISSION_TRANSLATIONS.get(perm, perm) for perm in error.missing_permissions]
            missing_perms_str = ", ".join(missing_perms)
            await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> 権限がありません。", description=f"権限を持っている人が実行してください。\n必要な権限リスト: {missing_perms_str}", color=discord.Color.red()), ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> 権限がありません。", description="権限がないか、\nあなた(サーバー)がBotからBANされているため実行できません。", color=discord.Color.red()), ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a
        else:
            if f"```{error}```" == "``````":
                a = None
                return a
            msg = await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> 予期しないエラーが発生しました。", description=f"```{error}```", color=discord.Color.red()).set_footer(text="サポートサーバーへお問い合わせください。"), view=discord.ui.View().add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk")))

async def setup(bot):
    await bot.add_cog(AdminCog(bot))