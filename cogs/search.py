from discord.ext import commands, tasks
import discord
from discord import app_commands
import traceback
import ssl
import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup
import os
import re
import random
import aiohttp
from PIL import Image, ImageSequence, ImageEnhance, ImageDraw, ImageFont, ImageOps
import textwrap
import unicodedata
import requests
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
import sys
import pyshorteners
import logging
import time
from functools import partial
import json
import asyncio
from urllib.parse import urlparse
import ast
import operator
from yt_dlp import YoutubeDL
import io
import pykakasi
from deep_translator import GoogleTranslator
import discord_emoji

# サポートする演算子を定義
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

COOLDOWN_TIME_TRANSEMOJI = 3
cooldown_transemoji_time = {}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = YoutubeDL(YTDL_OPTIONS)

class NomTranslater():
    def __init__(self):
        self.se = requests.Session()
        self.index = self.se.get("https://racing-lagoon.info/nomu/translate.php").text
        self.bs = BeautifulSoup(self.index, 'html.parser')
        self.token = self.bs.find({"input": {"name": "token"}})["value"]

    def translare(self, text: str):

        data = {
            'token': self.token,
            'before': text,
            'level': '2',
            'options': 'nochk',
            'transbtn': '翻訳',
            'after1': '',
            'options_permanent': '',
            'new_japanese': '',
            'new_nomulish': '',
            'new_setugo': '',
            'setugo': 'settou',
        }

        nom_index = self.se.post('https://racing-lagoon.info/nomu/translate.php', data=data)

        bs = BeautifulSoup(nom_index.text, 'html.parser')

        return bs.find_all({"textarea": {"class": "maxfield outputfield form-control selectAll"}})[1].get_text()

class YTDL():
    def __init__(self, url: str):
        self.url = url
        pass

    async def build(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'accept': '*/*',
                'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
                'content-type': 'text/plain;charset=UTF-8',
                'origin': 'https://transkriptor.com',
                'priority': 'u=1, i',
                'referer': 'https://transkriptor.com/',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            }

            data = '{"url":"' + self.url +'","app":"transkriptor","is_only_download":true}'
            async with session.post("https://oo6o8y6la6.execute-api.eu-central-1.amazonaws.com/default/Upload-DownloadYoutubeLandingPage", headers=headers, data=data) as resp:
                try:
                    response_text = await resp.text()
                    url_data = json.loads(response_text)
                    return url_data["download_url"]
                except json.JSONDecodeError as e:
                    print(f"JSON デコードエラー: {e}")
                    print(f"レスポンス内容: {response_text}")
                    return None
                except KeyError as e:
                    print(f"キーエラー: '{e}' がレスポンスにありませんでした。")
                    print(f"レスポンス内容: {response_text}")
                    return None

class SafeCalculator(ast.NodeVisitor):
    def visit_BinOp(self, node):
        # 左右のノードを再帰的に評価
        left = self.visit(node.left)
        right = self.visit(node.right)
        # 演算子を取得して評価
        operator_type = type(node.op)
        if operator_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[operator_type](left, right)
        return "エラー。"

    def visit_Num(self, node):
        return node.n

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit_Expr(node)
        elif isinstance(node, ast.BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, ast.Constant):  # Python 3.8以降
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7以前
            return self.visit_Num(node)
        else:
            return "エラー。"

def safe_eval(expr):
    try:
        tree = ast.parse(expr, mode='eval')
        calculator = SafeCalculator()
        return calculator.visit(tree.body)
    except Exception as e:
        return f"Error: {e}"

class Download():
    def __init__(self, url: str):
        self.url = url
        pass

    def twitter(self):
        ydl_opts = {
            'quiet': True,
            'skip_download': True
        }

        url = self.url

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if "formats" in info:
                for fmt in info["formats"]:
                    if ".mp4" in fmt.get('url'):
                        return info.get("title"), fmt.get('url')
                    
                return info.get("title"), None

class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.imgurclientid = self.tkj["ImgurClientID"]
        print(f"init -> SearchCog")

    async def get_user_savedata(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind
    
    async def get_user_point(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        return dbfind["count"]

    async def get_user_tag_(self, user: discord.User):
        db = self.bot.async_db["Main"].UserTag
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return "称号なし"
        if dbfind is None:
            return "称号なし"
        return dbfind["Tag"]

    async def get_user_color(self, user: discord.User):
        db = self.bot.async_db["Main"].UserColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return discord.Color.green()
        if dbfind is None:
            return discord.Color.green()
        if dbfind["Color"] == "red":
            return discord.Color.red()
        elif dbfind["Color"] == "yellow":
            return discord.Color.yellow()
        elif dbfind["Color"] == "blue":
            return discord.Color.blue()
        elif dbfind["Color"] == "random":
            return discord.Color.random()
        return discord.Color.green()

    async def get_connect_data(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginConnectData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        if dbfind is None:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        return {"Youtube": dbfind["youtube"], "Twitter": dbfind["X"]}

    async def gold_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotGoldPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0
        
    async def pfact_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotPointFactory
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0

    async def get_bot_adder_from_audit_log(self, guild: discord.Guild, bot_user: discord.User):
        if not bot_user.bot:
            return "Botではありません。"
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=None):
                if entry.target == bot_user:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました: {e}"

    async def roles_get(self, guild: discord.Guild, user: discord.User):
        try:
            mem = await guild.fetch_member(user.id)
            return "**ロール一覧**: " + " ".join([f"{r.mention}" for r in mem.roles])
        except:
            return "**ロール一覧**: このサーバーにいません。"

    @commands.hybrid_group(name="search", description="ユーザー情報を見ます。", fallback="user")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def user_search(self, ctx: commands.Context, user: discord.User):
        await ctx.defer()
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            isguild = None
            isbot = None
            if ctx.guild.get_member(user.id):
                isguild = "います。"
            else:
                isguild = "いません。"
            if user.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"
            permissions = "ユーザー"
            try:
                if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(user.id).roles:
                    permissions = "モデレーター"
                if user.id == 1335428061541437531:
                    permissions = "管理者"
                if user.id == 1346643900395159572:
                    permissions = "SharkBot"
            except:
                pass
            add_bot_user = await self.get_bot_adder_from_audit_log(ctx.guild, user)
            tag = await self.get_user_tag_(user)
            col = await self.get_user_color(user)
            embed = discord.Embed(title=f"{user.display_name}の情報 (ページ1)", color=col)
            embed.add_field(name="基本情報", value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**\n認証Bot？: **{"はい" if user.public_flags.verified_bot else "いいえ"}**").add_field(name="サービス情報", value=f"権限: **{permissions}**")
            userdata = await self.get_user_savedata(user)
            if userdata:
                guild = int(userdata["Guild"])
                logininfo = f"**言語**: {userdata["Lang"]}\n"
                if self.bot.get_guild(guild):
                    gu = self.bot.get_guild(guild)
                    logininfo += f"**最後に認証したサーバーの名前**: {gu.name}\n"
                    logininfo += f"**最後に認証したサーバーのid**: {gu.id}"
                embed.add_field(name="ログイン情報", value=logininfo, inline=False)
                pre = userdata["Nitro"]
                if pre == 0:
                    embed.add_field(name="Nitro", value="なし", inline=False)
                elif pre == 1:
                    embed.add_field(name="Nitro", value="Nitro Classic", inline=False)
                elif pre == 2:
                    embed.add_field(name="Nitro", value="Nitro", inline=False)
                elif pre == 3:
                    embed.add_field(name="Nitro", value="Nitro Basic", inline=False)
            embed.add_field(name="その他のAPIからの情報", value=f"""
スパムアカウントか？: {"✅" if user.public_flags.spammer else "❌"}
アクティブデベロッパーか？: {"✅" if user.public_flags.active_developer else "❌"}
Discordスタッフか？: {"✅" if user.public_flags.staff else "❌"}
Discordパートナーか？: {"✅" if user.public_flags.partner else "❌"}
HypeSquadEventsメンバーか？: {"✅" if user.public_flags.hypesquad else "❌"}
バグハンターか？: {"✅" if user.public_flags.bug_hunter else "❌"}
バグハンターLv2か？: {"✅" if user.public_flags.bug_hunter_level_2 else "❌"}
HypeSquadBraveryメンバーか？: {"✅" if user.public_flags.hypesquad_bravery else "❌"}
HypeSquadBrillianceメンバーか？: {"✅" if user.public_flags.hypesquad_brilliance else "❌"}
HypeSquadBalanceメンバーか？: {"✅" if user.public_flags.hypesquad_balance else "❌"}
早期サポーターか？: {"✅" if user.public_flags.early_supporter else "❌"}
早期チームユーザーか？: {"✅" if user.public_flags.team_user else "❌"}
システムユーザーか？: {"✅" if user.public_flags.system else "❌"}
早期認証Botデベロッパーか？: {"✅" if user.public_flags.verified_bot_developer else "❌"}
Discord認定モデレーターか？: {"✅" if user.public_flags.discord_certified_moderator else "❌"}
Botを追加したユーザーは？: {add_bot_user}
""", inline=False)
            embed2 = discord.Embed(title=f"{user.display_name}の情報 (ページ2)", color=col)
            point_check = await self.get_user_point(user)
            embed2.add_field(name="Sharkポイント", value=f"{point_check}P", inline=True)
            gold_check = await self.gold_user_data(user)
            embed2.add_field(name="錬金術研究所", value=f"{gold_check}個", inline=True)
            pfact = await self.pfact_user_data(user)
            embed2.add_field(name="ポイント工場", value=f"{pfact}個", inline=True)
            embed2.add_field(name="称号", value=f"{tag}", inline=True)
            if not user.mutual_guilds == []:
                if not user.id == self.bot.user.id:
                    gl = [f"{g.name} / {g.id}" for g in user.mutual_guilds][:15]
                    embed2.add_field(name="Botと一緒にいるサーバー(15件まで)", inline=False, value="\n".join(gl))
            embed2.set_image(url=user.banner.url if user.banner else None)
            roles = await self.roles_get(ctx.guild, user)
            embed3 = discord.Embed(title=f"{user.display_name}の情報 (ページ3)", color=discord.Color.green(), description=roles)
            pages = [embed, embed2, embed3]
            class PaginatorView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.current_page = 0
                    self.message = None

                async def update_message(self, interaction: discord.Interaction):
                    await interaction.response.edit_message(embed=pages[self.current_page], view=self)

                @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
                async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page > 0:
                        self.current_page -= 1
                        await self.update_message(interaction)

                @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
                async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page < len(pages) - 1:
                        self.current_page += 1
                        await self.update_message(interaction)

            view = PaginatorView()
            view.add_item(discord.ui.Button(label="/shopでSharkポイントを使って装飾アイテムを買えます。", disabled=True))
            view.add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"))
            if user.avatar:
                await ctx.reply(embed=embed.set_thumbnail(url=user.avatar.url), view=view)
            else:
                await ctx.reply(embed=embed.set_thumbnail(url=user.default_avatar.url), view=view)
        except:
            return await ctx.reply(f"{sys.exc_info()}")
        
    async def guild_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            guilds = []
            for gu in interaction.user.mutual_guilds:
                guilds.append(gu)
            choices = []

            for guild in guilds:
                if current.lower() in guild.name.lower():
                    choices.append(discord.app_commands.Choice(name=guild.name[:100], value=str(guild.id)))

                if len(choices) >= 25:
                    break

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @user_search.command(name="guild", description="サーバーの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @discord.app_commands.autocomplete(サーバー=guild_autocomplete)
    async def guild_info(self, ctx: commands.Context, サーバー: str = None):
        await ctx.defer()
        if not サーバー:
            embed = discord.Embed(title=f"{ctx.guild.name}の情報", color=discord.Color.green())
            embed.add_field(name="サーバー名", value=ctx.guild.name)
            embed.add_field(name="サーバーID", value=str(ctx.guild.id))
            embed.add_field(name="チャンネル数", value=f"{len(ctx.guild.channels)}個")
            embed.add_field(name="メンバー数", value=f"{ctx.guild.member_count}人")
            embed.add_field(name="Nitroブースト", value=f"{ctx.guild.premium_subscription_count}人")
            embed.add_field(name="オーナー名", value=ctx.guild.owner.name if ctx.guild.owner else "取得失敗")
            embed.add_field(name="オーナーID", value=str(ctx.guild.owner_id))
            JST = datetime.timezone(datetime.timedelta(hours=9))
            embed.add_field(name="作成日", value=ctx.guild.created_at.astimezone(JST))
            try:
                disboard = [str(m.id) for m in ctx.guild.members if m.id == 302050872383242240]
                dissoku = [str(m.id) for m in ctx.guild.members if m.id == 761562078095867916]
                view = discord.ui.View()
                if not disboard == []:
                    view.add_item(discord.ui.Button(label="参加する (Disboard)", url=f"https://disboard.org/ja/server/join/{ctx.guild.id}"))
                if not dissoku == []:
                    view.add_item(discord.ui.Button(label="参加する (Dissoku)", url=f"https://app.dissoku.net/api/guilds/{ctx.guild.id}/join"))
            except:
                pass
            embed.set_footer(text="SharkBot経由")
            if ctx.guild.icon:
                await ctx.reply(embed=embed.set_thumbnail(url=ctx.guild.icon.url), view=view)
            else:
                await ctx.reply(embed=embed, view=view)
        else:
            サーバー_ = self.bot.get_guild(int(サーバー))
            if サーバー_:
                embed = discord.Embed(title=f"{サーバー_.name}の情報", color=discord.Color.green())
                embed.add_field(name="サーバー名", value=サーバー_.name)
                embed.add_field(name="サーバーID", value=str(サーバー_.id))
                embed.add_field(name="チャンネル数", value=f"{len(サーバー_.channels)}個")
                embed.add_field(name="メンバー数", value=f"{サーバー_.member_count}人")
                embed.add_field(name="Nitroブースト", value=f"{サーバー_.premium_subscription_count}人")
                embed.add_field(name="オーナー名", value=サーバー_.owner.name if サーバー_.owner else "取得失敗")
                embed.add_field(name="オーナーID", value=str(サーバー_.owner_id))
                JST = datetime.timezone(datetime.timedelta(hours=9))
                embed.add_field(name="作成日", value=サーバー_.created_at.astimezone(JST))
                view = discord.ui.View()
                try:
                    disboard = [str(m.id) for m in サーバー_.members if m.id == 302050872383242240]
                    dissoku = [str(m.id) for m in サーバー_.members if m.id == 761562078095867916]
                    if not disboard == []:
                        view.add_item(discord.ui.Button(label="参加する (Disboard)", url=f"https://disboard.org/ja/server/join/{サーバー_.id}"))
                    if not dissoku == []:
                        view.add_item(discord.ui.Button(label="参加する (Dissoku)", url=f"https://app.dissoku.net/api/guilds/{サーバー_.id}/join"))
                except:
                    pass
                embed.set_footer(text="SharkBot経由")
                if サーバー_.icon:
                    await ctx.reply(embed=embed.set_thumbnail(url=サーバー_.icon.url), view=view)
                else:
                    await ctx.reply(embed=embed, view=view)
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://app.dissoku.net/api/guilds/{サーバー}') as response:
                        if not response.status == 200:
                            return await ctx.reply(embed=discord.Embed(title="取得失敗！", color=discord.Color.red()))
                        guild = await response.json()
                        embed = discord.Embed(title=f"{guild.get("name", "取得失敗")}の情報", color=discord.Color.green())
                        embed.add_field(name="サーバー名", value=str(guild.get("name", "取得失敗")))
                        embed.add_field(name="サーバーID", value=str(guild.get("id", "取得失敗")))
                        embed.add_field(name="サーバー人数", value=str(guild.get("membernum", "取得失敗")))
                        embed.add_field(name="作成日", value=str(guild.get("created_at", "取得失敗")))
                        embed.add_field(name="オーナーID", value=str(guild.get("owner", "取得失敗")))
                        owner = await commands.UserConverter().convert(ctx, str(guild.get("owner", "取得失敗")))
                        embed.add_field(name="オーナー名", value=owner.name)
                        embed.set_thumbnail(url=guild.get("icon_url", ctx.author.default_avatar.url))
                        embed.set_footer(text="API経由")
                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="参加する", url=f"https://app.dissoku.net/api/guilds/{サーバー}/join"))
                        return await ctx.reply(embed=embed, view=view)

    async def block_check_search(self, user: discord.User):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return False
        if not dbfind is None:
            return True
        return False
    
    async def get_ban_user_from_audit_log(self, guild: discord.Guild, user: discord.User):
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=None):
                if entry.target.id == user.id:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました: {e}"

    @user_search.command(name="ban", description="このサーバーでBanされたユーザー情報を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban_info(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        try:
            ban_user = await ctx.guild.fetch_ban(ユーザー)
            embed = discord.Embed(title="BANされたユーザーの情報", color=discord.Color.green())
            embed.add_field(name="ユーザー名", value=f"{ban_user.user.display_name} ({ban_user.user.id})", inline=False)
            embed.add_field(name="ユーザーid", value=f"{ban_user.user.id}", inline=False)
            embed.add_field(name="BANされた理由", value=ban_user.reason if ban_user.reason else "理由なし")
            User = await self.get_ban_user_from_audit_log(ctx.guild, ユーザー)
            embed.add_field(name="BANした人", value=User, inline=False)
            embed.set_thumbnail(url=ban_user.user.avatar.url if ban_user.user.avatar else ban_user.user.default_avatar.url)
            embed.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}")
            await ctx.reply(embed=embed)
        except discord.NotFound:
            await ctx.reply(embed=discord.Embed(title="その人はBANされていません。", color=discord.Color.red()))

    @user_search.command(name="mute", description="ミュートされたユーザーの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def mute_info(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        check = await self.block_check_search(ユーザー)
        if not check:
            return await ctx.reply(embed=discord.Embed(title="そのユーザーはMuteされていません。", color=discord.Color.red()))
        embed = discord.Embed(title=f"ミュート情報", color=discord.Color.yellow())
        embed.add_field(name="ユーザー名", value=f"{ユーザー.name}")
        embed.add_field(name="ミュート済みか？", value=f"はい。")
        if not ユーザー.mutual_guilds == []:
            gl = [f"{g.name} / {g.id}" for g in ユーザー.mutual_guilds][:15]
            embed.add_field(name="Botと一緒にいるサーバー(15件まで)", inline=False, value="\n".join(gl))
        embed.set_thumbnail(url=ユーザー.avatar.url if ユーザー.avatar else ユーザー.default_avatar.url)
        return await ctx.reply(embed=embed)

    @user_search.command(name="avatar", description="アバターを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def avatar_info(self, ctx: commands.Context, avatar: discord.User):
        await ctx.defer()
        if avatar.avatar == None:
            return await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんのアバター", description=f"ダウンロード\n[.png]({avatar.default_avatar.with_format("png").url})", color=discord.Color.green()).set_image(url=avatar.default_avatar.url))
        await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんのアバター", description=f"ダウンロード\n[.png]({avatar.avatar.with_format("png").url}) [.jpg]({avatar.avatar.with_format("jpg").url}) [.webp]({avatar.avatar.with_format("webp").url})", color=discord.Color.green()).set_image(url=avatar.avatar.url))

    @user_search.command(name="asset", description="アバターの装飾を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def avatar_asset(self, ctx: commands.Context, avatar: discord.User):
        if avatar.avatar_decoration == None:
            return await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんの装飾", description="装飾が見つかりません", color=discord.Color.red()))
        await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんの装飾", color=discord.Color.green()).set_image(url=avatar.avatar_decoration.url))

    @user_search.command(name="embed", description="Embedの情報を見るよ")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def embed_info(self, ctx: commands.Context, メッセージid: str):
        await ctx.defer()
        message = await ctx.channel.fetch_message(int(メッセージid))
        if not message.embeds:
            return await ctx.reply(embed=discord.Embed(title="Embedが見つかりません。", color=discord.Color.red()))
        embed = message.embeds[0].to_dict()
        await ctx.reply(embed=discord.Embed(title="Embedの情報", description=f"```{embed}```", color=discord.Color.green()))

    @user_search.command(name="emoji", description="絵文字の情報を見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def emoji_info(self, ctx: commands.Context, 絵文字: discord.Emoji):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="絵文字情報", color=discord.Color.green()).set_image(url=絵文字.url).add_field(name="基本情報", value=f"名前: {絵文字.name}\n作成日時: {絵文字.created_at}", inline=False).add_field(name="サーバー情報", value=f"{絵文字.guild.name} ({絵文字.guild.id})", inline=False))

    @user_search.command(name="snapshot", description="転送の情報を見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def snapshot_info(self, ctx: commands.Context, メッセージ: discord.Message):
        await ctx.defer()
        if メッセージ.message_snapshots:
            snap = メッセージ.message_snapshots[0]
            await ctx.reply(embed=discord.Embed(title="転送の情報", description=f"内容:\n{snap.content}\n作成日: **{snap.created_at}**", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(title="転送の情報", description=f"転送が見つかりませんでした。", color=discord.Color.red()))

    @user_search.command(name="permission", description="権限を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def permission_search(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
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
        user_perms = [PERMISSION_TRANSLATIONS.get(perm, perm) for perm, value in メンバー.guild_permissions if value]
        user_perms_str = ", ".join(user_perms)
        avatar = メンバー.avatar.url if メンバー.avatar else メンバー.display_avatar.url
        await ctx.reply(embed=discord.Embed(title=f"{メンバー.name}さんの権限", description=user_perms_str, color=discord.Color.green()).set_thumbnail(url=avatar))

    async def get_music_info(self, url):
        loop = asyncio.get_running_loop()
        try:
            info = await loop.run_in_executor(None, partial(ytdl.extract_info, url, download=False, process=False))
            if not info:
                return None
            info["url"] = url
            info["time"] = time.time() + 60 * 60 * 24 * 7
            return info
        except Exception as e:
            print(f"Error fetching music info: {e}", file=sys.stderr)
            return None

    @user_search.command(name="youtube", description="youtube動画の情報を見るよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def search_youtube(self, ctx: commands.Context, url: str):
        await ctx.defer()
        dl_url = await YTDL(url).build()
        info = await self.get_music_info(url)
        loop = asyncio.get_running_loop()
        s = await loop.run_in_executor(None, partial(pyshorteners.Shortener))
        url_ = await loop.run_in_executor(None, partial(s.tinyurl.short, dl_url))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="動画URL", url=f"{url}"))
        view.add_item(discord.ui.Button(label="ダウンロード", url=url_))
        view.add_item(discord.ui.Button(label="チャンネルurl", url=info['channel_url']))
        view.add_item(discord.ui.Button(label="チャンネル登録", url=f"https://www.youtube.com/channel/{info['channel_id']}?sub_confirmation=1"))
        embed = discord.Embed(title="Youtube動画の情報", color=discord.Color.green()).add_field(name="タイトル", value=info["title"], inline=False).set_image(url=info["thumbnail"])
        embed.add_field(name="チャンネル名", value=info['channel'], inline=True)
        embed.add_field(name="チャンネルid", value=info['channel_id'], inline=True)
        await ctx.reply(embed=embed, view=view)

    @user_search.command(name="twitter-video", description="twitterの動画の情報を取得するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def search_twittervideo(self, ctx: commands.Context, url: str):
        await ctx.defer()
        download = Download(url)
        loop = asyncio.get_running_loop()
        title, dl_url = await loop.run_in_executor(None, partial(download.twitter))
        s = await loop.run_in_executor(None, partial(pyshorteners.Shortener))
        url_ = await loop.run_in_executor(None, partial(s.tinyurl.short, dl_url))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="ダウンロード", url=url_))
        await ctx.reply(embed=discord.Embed(title="Twitterの動画の情報", color=discord.Color.green()).add_field(name="タイトル", value=title, inline=False), view=view)

    @user_search.command(name="translate", description="翻訳をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(翻訳先=[
        app_commands.Choice(name='日本語へ',value="ja"),
        app_commands.Choice(name='英語へ',value="en"),
        app_commands.Choice(name='中国語へ',value="zh-CN"),
        app_commands.Choice(name='韓国語へ',value="ko"),
        app_commands.Choice(name='ロシア語へ',value="ru"),
        app_commands.Choice(name='ノムリッシュ語へ',value="nom"),
    ])
    async def translate(self, ctx: commands.Context, 翻訳先: app_commands.Choice[str], *, テキスト: str):
        await ctx.defer()

        if 翻訳先.value == "nom":
            loop = asyncio.get_running_loop()
            nom = await loop.run_in_executor(None, partial(NomTranslater))
            text = await loop.run_in_executor(None, partial(nom.translare, テキスト))

            embed = discord.Embed(
                title=f"翻訳 (ノムリッシュ語へ)",
                description=f"```{text}```",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
            return

        try:
            translator = GoogleTranslator(source="auto", target=翻訳先.value)
            translated_text = translator.translate(テキスト)

            embed = discord.Embed(
                title=f"翻訳 ({翻訳先.value} へ)",
                description=f"```{translated_text}```",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="翻訳に失敗しました",
                description="指定された言語コードが正しいか確認してください。",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)

    @user_search.command(name="news", description="ニュースを表示します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def news(self, ctx: commands.Context):
        await ctx.defer()
        connector = ProxyConnector.from_url('socks5://127.0.0.1:9150')
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f'https://mainichi.jp/', ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.find_all('div', class_="toppickup")[0]
                url = title.find_all('a')[0]
                await ctx.reply(f"https:{url["href"]}")

    @user_search.command(name="eew", description="地震速報を表示します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def news(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.p2pquake.net/v2/history?codes=551&limit=1', ssl=ssl_context) as response:
                js = json.loads(await response.text())
                await ctx.reply(embed=discord.Embed(title=f"{js[0]["earthquake"]["hypocenter"]["name"]}の地震", description=f"発生場所: ```{"\n".join([ff["addr"] for ff in js[0]["points"]][:20])}\n...```", color=discord.Color.blue()).set_footer(text="地震速報").add_field(name="危険度", value=f"{js[0]["earthquake"]["domesticTsunami"]}").add_field(name="発生時間", value=f"{js[0]["earthquake"]["time"]}"))

    @user_search.command(name="safeweb", description="Webサイトが安全かどうかをチェックします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def safeweb(self, ctx: commands.Context, url: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://findredirect.com/api/redirects', json={
                'url': url
            }) as response_expand:
                js_short = await response_expand.json()

        async with aiohttp.ClientSession() as session_safeweb:
            if not js_short[0].get("redirect", False):

                q = urlparse(url).netloc
                async with session_safeweb.get(f'https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0', ssl=ssl_context) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await ctx.reply(embed=discord.Embed(title="このサイトは危険です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.red()))
                    elif js["rating"] == "w":
                        await ctx.reply(embed=discord.Embed(title="このサイトは注意が必要です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.yellow()))
                    elif js["rating"] == "g":
                        await ctx.reply(embed=discord.Embed(title="このサイトは評価されていません。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.blue()))
                    else:
                        await ctx.reply(embed=discord.Embed(title="このサイトは多分安全です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.green()))
            else:
                q = urlparse(js_short[0].get("redirect", False)).netloc
                async with session_safeweb.get(f'https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0', ssl=ssl_context) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await ctx.reply(embed=discord.Embed(title="このサイトは危険です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.red()))
                    elif js["rating"] == "w":
                        await ctx.reply(embed=discord.Embed(title="このサイトは注意が必要です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.yellow()))
                    elif js["rating"] == "g":
                        await ctx.reply(embed=discord.Embed(title="このサイトは評価されていません。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.blue()))
                    else:
                        await ctx.reply(embed=discord.Embed(title="このサイトは多分安全です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.green()))

    @user_search.command(name="wikipedia", description="WikiPediaを検索します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def weikipedia_search(self, ctx: commands.Context, 検索ワード: str):
        await ctx.defer()
        loop = asyncio.get_event_loop()
        try:
            
            wikipedia_api_url = "https://ja.wikipedia.org/w/api.php"
            
            # APIパラメータ
            params = {
                "action": "query",
                "format": "json",
                "titles": 検索ワード,
                "prop": "info",
                "inprop": "url"
            }
            
            response = await loop.run_in_executor(None, partial(requests.get, wikipedia_api_url, params=params))
            await loop.run_in_executor(None, partial(response.raise_for_status))
            data = await loop.run_in_executor(None, partial(response.json))
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                await ctx.send(f"Wikipedia記事が見つかりませんでした。")
                return
            
            page_id, page_info = next(iter(pages.items()))
            if page_id == "-1":
                await ctx.send(f"Wikipedia記事が見つかりませんでした。")
                return
            
            short_url = f"https://ja.wikipedia.org/w/index.php?curid={page_id}"
            await ctx.send(f"🔗 Wikipedia短縮リンク: {short_url}")
        
        except Exception as e:
            await ctx.send(f"エラーが発生しました: {str(e)}")

    @user_search.command(name="imgur", description="画像を検索します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def imgur(self, ctx: commands.Context, 検索ワード: str):
        await ctx.defer()
        try:
            params = {
                'client_id': f'{self.imgurclientid}',
                'inflate': 'tags',
                'q': f'{検索ワード}',
                'types': 'users,tags,posts',
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, partial(requests.get, 'https://api.imgur.com/3/suggest', params=params))
            data = await loop.run_in_executor(None, partial(response.json))

            if not data["data"]["posts"]:
                return await ctx.reply("検索結果が見つかりませんでした。")

            post_hash = data["data"]["posts"][0]["hash"]

            headers = {"Authorization": f"Client-ID {self.imgurclientid}"}
            gallery_response = await loop.run_in_executor(None, partial(requests.get, f"https://api.imgur.com/3/gallery/{post_hash}", headers=headers))
            gallery_data = await loop.run_in_executor(None, partial(gallery_response.json))

            if "images" in gallery_data["data"] and gallery_data["data"]["images"]:
                image_url = gallery_data["data"]["images"][0]["link"]
            else:
                image_url = f"https://imgur.com/gallery/{post_hash}"

            return await ctx.reply(f"{image_url}")
        except:
            return await ctx.reply(f"検索に失敗しました。")
        
    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add_translate(self, reaction: discord.Reaction, user: discord.Member):
        if user.bot:  # Botのリアクションは無視
            return

        db = self.bot.async_db["Main"].EmojiTranslate
        try:
            dbfind = await db.find_one({"Guild": reaction.message.guild.id}, {"_id": False})
        except Exception as e:
            print(f"DBエラー: {e}")
            return

        if dbfind is None:
            return

        current_time = time.time()
        last_message_time = cooldown_transemoji_time.get(reaction.message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_TRANSEMOJI:
            return
        cooldown_transemoji_time[reaction.message.guild.id] = current_time

        content = reaction.message.content
        if not content and reaction.message.embeds:
            content = reaction.message.embeds[0].description

        if not content:
            return  # 翻訳対象がない場合は何もしない

        lang_map = {
            "🇯🇵": "ja",
            "🇺🇸": "en",
        }

        if reaction.emoji in lang_map:
            target_lang = lang_map[reaction.emoji]
            msg = await reaction.message.channel.send(
                embed=discord.Embed(title="🔄 翻訳中...", color=discord.Color.blue())
            )

            try:
                translator = GoogleTranslator(source="auto", target=target_lang)
                translated_text = translator.translate(content)
                await msg.edit(
                    embed=discord.Embed(
                        title=f"翻訳結果 ({target_lang})",
                        description=f"```{translated_text}```",
                        color=discord.Color.green()
                    )
                )
            except Exception as e:
                print(f"翻訳エラー: {e}")
                await msg.edit(
                    embed=discord.Embed(
                        title="翻訳に失敗しました",
                        color=discord.Color.red()
                    )
                )

    @user_search.command(name="library", description="Pythonライブラリを検索します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def library_search(self, ctx: commands.Context, 検索ワード: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pypi.org/pypi/{検索ワード}/json') as response:
                js = await response.json()
                view=discord.ui.View()
                view.add_item(discord.ui.Button(label="アクセスする", url=js["info"]["package_url"]))
                await ctx.reply(view=view, embed=discord.Embed(title=f"{検索ワード}", url=js["info"]["package_url"], color=discord.Color.green()).add_field(name="バージョン", value=js["info"]["version"]).set_footer(text="Pypi", icon_url="https://cdn.takasumibot.com/images/pypi.png"))

async def fetch_avatar(user: discord.User):
    if user.avatar:
        url_a = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar.key}"
    else:
        url_a = user.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(url_a, timeout=10) as resp:
            return await resp.read()

def PILF_getsize(font: ImageFont.FreeTypeFont, text):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def wrap_text_with_ellipsis(text, font, draw, max_width, max_height, line_height):
    lines = []
    for raw_line in text.split("\n"):
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char

            if len(lines) * line_height >= max_height - line_height * 2:
                ellipsis = "…"
                while True:
                    bbox = draw.textbbox((0, 0), current_line + ellipsis, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        break
                    if len(current_line) == 0:
                        break
                    current_line = current_line[:-1]
                lines.append(current_line + ellipsis)
                return lines

        if current_line:
            lines.append(current_line)

    return lines

def draw_mixed_text(draw, text, position, text_font, emoji_font, fill, spacing=0):
    x, y = position

    text_ = discord_emoji.to_unicode_multi(text)

    for char in text_:
        is_emoji = "EMOJI" in unicodedata.name(char, "") or ord(char) >= 0x1F000
        font = emoji_font if is_emoji else text_font

        bbox = font.getbbox(char)
        width = bbox[2] - bbox[0]

        draw.text((x, y), char, font=font, fill=fill)
        x += width + spacing

def create_quote_image(int_: discord.Interaction, author, text, avatar_bytes, background, textcolor, color: bool):
        width, height = 800, 400
        background_color = background
        text_color = textcolor

        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)

        avatar_size = (400, 400)
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize(avatar_size)

        mask = Image.new("L", avatar_size, 255)
        for x in range(avatar_size[0]):
            alpha = 255 if x < avatar_size[0] // 2 else int(255 * (1 - (x - avatar_size[0] // 2) / (avatar_size[0] / 2)))
            for y in range(avatar_size[1]):
                mask.putpixel((x, y), alpha)
        avatar.putalpha(mask)

        img.paste(avatar, (0, height - avatar_size[1]), avatar)

        try:
            font = ImageFont.truetype("data/DiscordFont.ttf", 30)
            emoji_font = ImageFont.truetype("data/Emoji.ttf", 30)
            name_font = ImageFont.truetype("data/DiscordFont.ttf", 20)
        except:
            font = ImageFont.load_default()
            emoji_font = ImageFont.load_default()
            name_font = ImageFont.load_default()

        text_x = 420
        max_text_width = width - text_x - 50

        max_text_height = height - 80
        line_height = font.size + 10

        def replace_mention_with_id(match):
            return int_.client.get_user(int(match.group(1))).display_name
        
        def replace_mention_with_channel_id(match):
            return int_.client.get_channel(int(match.group(1))).name

        lines = wrap_text_with_ellipsis(re.sub(r"<#(\d+)>", replace_mention_with_channel_id, re.sub(r"<@!?(\d+)>", replace_mention_with_id, text)), font, draw, max_text_width, max_text_height, line_height)

        total_lines = len(lines)
        line_height = font.size + 10
        text_block_height = total_lines * line_height
        text_y = (height - text_block_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            draw_mixed_text(draw, line, ((width + text_x - 50 - line_width) // 2, text_y + i * line_height), emoji_font=emoji_font, fill=text_color, text_font=font)
            # draw.text(
                #((width + text_x - 50 - line_width) // 2, text_y + i * line_height),
                #line,
                #fill=text_color,
                #font=font
            #)

        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=name_font)
        author_width = bbox[2] - bbox[0]
        author_x = (width + text_x - 50 - author_width) // 2
        author_y = text_y + len(lines) * line_height + 10

        draw.text((author_x, author_y), author_text, font=name_font, fill=text_color)

        draw.text((700, 0), "SharkBot", font=name_font, fill=text_color)

        if color:

            return img
        else:
            return img.convert("L")

class MiqColor(discord.ui.View):
    def __init__(self, author: discord.User, message: discord.Message, timeout=180):
        super().__init__(timeout=timeout)
        self.message = message
        self.author = author
        self.faked = False
        self.colord = True
        self.back_color_ = (0, 0, 0)
        self.text_color = (255, 255, 255)

    @discord.ui.button(emoji="<:Delete:1362275962967953570>", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self.author.id == interaction.user.id:
            return
        await interaction.message.edit(content=f"<:Success:1362271281302601749> 削除しました。", view=None, attachments=[])

    @discord.ui.button(emoji="<:Color:1362272545377751230>", style=discord.ButtonStyle.green)
    async def color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self.author.id == interaction.user.id:
            return
        try:
            if not self.colord:
                if self.faked:
                    av = await fetch_avatar(interaction.user)
                    miq = create_quote_image(
                        interaction,
                        interaction.user.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        True
                    )
                    button.style = discord.ButtonStyle.success
                else:
                    av = await fetch_avatar(self.message.author)
                    miq = create_quote_image(
                        interaction,
                        self.message.author.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        True
                    )
                    button.style = discord.ButtonStyle.gray
                self.colord = True
            else:
                if self.faked:
                    av = await fetch_avatar(interaction.user)
                    miq = create_quote_image(
                        interaction,
                        interaction.user.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        False
                    )
                    button.style = discord.ButtonStyle.success
                else:
                    av = await fetch_avatar(self.message.author)
                    miq = create_quote_image(
                        interaction,
                        self.message.author.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        False
                    )
                    button.style = discord.ButtonStyle.gray
                self.colord = False
            with io.BytesIO() as image_binary:
                miq.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='quote.png')
                await interaction.message.edit(view=self, attachments=[file])
        except aiohttp.ClientOSError as e:
            return await interaction.message.edit(view=None, attachments=[], content="ClientOSエラーが発生しました。\n修正する見込みはありません。")

    @discord.ui.button(emoji="<:Fake:1362276665937494058>", style=discord.ButtonStyle.gray)
    async def fake(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self.author.id == interaction.user.id:
            return
        try:
            if not self.colord:
                if not self.faked:
                    av = await fetch_avatar(interaction.user)
                    miq = create_quote_image(
                        interaction,
                        interaction.user.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        False
                    )
                    button.style = discord.ButtonStyle.success
                    self.faked = True
                else:
                    av = await fetch_avatar(self.message.author)
                    miq = create_quote_image(
                        interaction,
                        self.message.author.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        False
                    )
                    button.style = discord.ButtonStyle.gray
                    self.faked = False
            else:
                if not self.faked:
                    av = await fetch_avatar(interaction.user)
                    miq = create_quote_image(
                        interaction,
                        interaction.user.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        True
                    )
                    button.style = discord.ButtonStyle.success
                    self.faked = True
                else:
                    av = await fetch_avatar(self.message.author)
                    miq = create_quote_image(
                        interaction,
                        self.message.author.display_name,
                        self.message.content,
                        av,
                        self.back_color_,
                        self.text_color,
                        True
                    )
                    button.style = discord.ButtonStyle.gray
                    self.faked = False
            with io.BytesIO() as image_binary:
                miq.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='quote.png')
                await interaction.message.edit(view=self, attachments=[file])
        except aiohttp.ClientOSError as e:
            return await interaction.message.edit(view=None, attachments=[], content="ClientOSエラーが発生しました。\n修正する見込みはありません。")

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="背景色の設定",
        options=[
            discord.SelectOption(label="黒"),
            discord.SelectOption(label="白"),
            discord.SelectOption(label="赤"),
            discord.SelectOption(label="緑"),
            discord.SelectOption(label="黄"),
            discord.SelectOption(label="青")
        ]
    )
    async def back_color(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id == self.author.id:
            try:
                self.back_color_ = (0, 0, 0)
                self.text_color = (255, 255, 255)
                if "黒" == select.values[0]:
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            interaction,
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                elif "白" == select.values[0]:
                    self.back_color_ = (255, 255, 255)
                    self.text_color = (0, 0, 0)
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            True
                        )
                elif "赤" == select.values[0]:
                    self.back_color_ =  (206, 100, 232)
                    self.text_color = (0, 0, 0)
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            interaction,
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                elif "緑" == select.values[0]:
                    self.back_color_ =  (85, 207, 95)
                    self.text_color = (0, 0, 0)
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            interaction,
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                elif "黄" == select.values[0]:
                    self.back_color_ =  (204, 207, 68)
                    self.text_color = (0, 0, 0)
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            interaction,
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                elif "青" == select.values[0]:
                    self.back_color_ =  (83, 65, 250)
                    self.text_color = (0, 0, 0)
                    if self.faked:
                        av = await fetch_avatar(interaction.user)
                        miq = create_quote_image(
                            interaction,
                            interaction.user.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                    else:
                        av = await fetch_avatar(self.message.author)
                        miq = create_quote_image(
                            interaction,
                            self.message.author.display_name,
                            self.message.content,
                            av,
                            self.back_color_,
                            self.text_color,
                            self.colord
                        )
                with io.BytesIO() as image_binary:
                    miq.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename='quote.png')
                    await interaction.message.edit(view=self, attachments=[file])
            except aiohttp.ClientOSError as e:
                return await interaction.message.edit(view=None, attachments=[], content="ClientOSエラーが発生しました。\n修正する見込みはありません。")

class MiqReload(discord.ui.View):
    def __init__(self, author: discord.User, message: discord.Message, timeout=180):
        super().__init__(timeout=timeout)
        self.message = message
        self.author = author

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.gray)
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self.author.id == interaction.user.id:
            return
        try:
            av = await fetch_avatar(self.message.author)
            miq = create_quote_image(
                interaction,
                self.message.author.display_name,
                self.message.content,
                av,
                (0, 0, 0),
                (255, 255, 255),
                True
            )
            with io.BytesIO() as image_binary:
                miq.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='quote.png')
                view = MiqColor(interaction.user, self.message)
                await interaction.message.edit(view=view, content=None, attachments=[file])
        except aiohttp.ClientOSError as e:
            return await interaction.followup.send(ephemeral=True, content="ClientOSエラーが発生しました。\n再度実行をお願いします。")

    @discord.ui.button(emoji="<:Delete:1362275962967953570>", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not self.author.id == interaction.user.id:
            return
        await interaction.message.delete()

async def add_reactions_from_text(message, text):
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

@app_commands.context_menu(name="Make it a Quote")
async def miq_command(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer()
    if not message.content:
        return await interaction.followup.send("メッセージがありません。", ephemeral=True)
    try:
        avatar = message.author
        av = await fetch_avatar(avatar)
        miq = create_quote_image(
            interaction,
            message.author.display_name,
            message.content,
            av,
            (0, 0, 0),
            (255, 255, 255),
            True
        )
        with io.BytesIO() as image_binary:
            miq.save(image_binary, 'PNG')
            image_binary.seek(0)
            view = MiqColor(interaction.user, message)
            await interaction.followup.send(file=discord.File(fp=image_binary, filename='quote.png'), view=view)
    except aiohttp.ClientOSError as e:
        return await interaction.followup.send(content="ClientOSエラーが発生しました。\n修正する見込みはありません。", view=MiqReload(interaction.user, message))
    except:
        return await interaction.followup.send(f"生成に失敗しました。\n{sys.exc_info()}")

@app_commands.context_menu(name="その他")
async def more_command(interaction: discord.Interaction, message: discord.Message):
    class MoreMessageCommand(discord.ui.View):
        def __init__(self, message: discord.Message):
            super().__init__(timeout=None)
            self.message = message

        @discord.ui.select(
            cls=discord.ui.Select,
            placeholder="そのメッセージに対して使用するコマンド",
            options=[
                discord.SelectOption(label="絵文字をつける"),
                discord.SelectOption(label="石破の声に変換"),
            ]
        )

        async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
            if select.values[0] == "石破の声に変換":
                await interaction.response.defer()
                if not self.message.content:
                    return await interaction.followup.send(ephemeral=True, content="メッセージの内容がありません。")
                encoded_text = quote(self.message.content, encoding="utf-8")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:5002/ishiba?text={encoded_text}") as q:
                        try:
                            f = await q.read()
                            file_data = io.BytesIO(f)
                            file_data.seek(0)
                            embed = discord.Embed(title="石破の声", color=discord.Color.green())
                            await interaction.followup.send(embed=embed, file=discord.File(file_data, "ishiba.mp3"))
                        except UnicodeDecodeError as e:
                            await interaction.followup.send(f"音声ファイルの読み込み中にエラーが発生しました。\n{e}")
            elif select.values[0] == "絵文字をつける":
                class AddEmoji(discord.ui.Modal, title='絵文字をつける'):
                    m = discord.ui.TextInput(
                        label='テキストを入力',
                        placeholder=f'OK',
                        style=discord.TextStyle.short,
                        required=True,
                        max_length=8
                    )

                    mid = discord.ui.TextInput(
                        label='メッセージIDを入力',
                        default=f"{self.message.id}",
                        style=discord.TextStyle.short,
                        required=True
                    )

                    async def on_submit(self, interaction: discord.Interaction):
                        await interaction.response.defer(ephemeral=True)
                        try:
                            msg = await interaction.channel.fetch_message(int(self.mid.value))
                        except:
                            return await interaction.followup.send("メッセージが見つかりませんでした。", ephemeral=True)
                        await add_reactions_from_text(msg, self.m.value)
                        await interaction.followup.send("絵文字をつけました。", ephemeral=True)
                await interaction.response.send_modal(AddEmoji())
    await interaction.response.send_message(ephemeral=True, view=MoreMessageCommand(message), embed=discord.Embed(title="その他のコンテキストメニュー", description="メッセージ版", color=discord.Color.blue()).set_footer(text=f"mid:{message.id}"))

class LockMessageRemove(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.gray)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return
        db = interaction.client.async_db["Main"].LockMessage
        result = await db.delete_one({
            "Channel": interaction.channel.id,
        })
        await interaction.message.delete()
        await interaction.followup.send("LockMessageを削除しました。", ephemeral=True)

    @discord.ui.button(emoji="👇", style=discord.ButtonStyle.gray)
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return
        db = interaction.client.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": interaction.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            await discord.PartialMessage(channel=interaction.channel, id=dbfind["MessageID"]).delete()
        except:
            pass
        await asyncio.sleep(1)
        msg = await interaction.channel.send(embed=discord.Embed(title=dbfind["Title"], description=dbfind["Desc"], color=discord.Color.random()), view=LockMessageRemove())
        await db.replace_one(
            {"Channel": interaction.channel.id, "Guild": interaction.guild.id}, 
            {"Channel": interaction.channel.id, "Guild": interaction.guild.id, "Title": dbfind["Title"], "Desc": dbfind["Desc"], "MessageID": msg.id}, 
            upsert=True
        )

    @discord.ui.button(emoji="🛠️", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return
        await interaction.message.delete()

    @discord.ui.button(emoji="❓", style=discord.ButtonStyle.gray)
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="固定メッセージのヘルプ", description="🗑️で固定メッセージを削除。\n👇で固定メッセージを一番下に持っていく。(Botの発言用)\n🛠️で1つのメッセージを削除します。(固定メッセージは残ります。)\n❓でヘルプを表示します。", color=discord.Color.blue()), ephemeral=True)

@app_commands.context_menu(name="メッセージ固定")
async def message_pin(interaction: discord.Interaction, message: discord.Message):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message(embed=discord.Embed(title="権限がありません。", color=discord.Color.red()), ephemeral=True)
    if not message.content:
        return await interaction.response.send_message(embed=discord.Embed(title="メッセージの内容がありません。", color=discord.Color.red()), ephemeral=True)
    msg = await interaction.channel.send(embed=discord.Embed(title="固定済みメッセージ", description=message.content[:1500], color=discord.Color.random()), view=LockMessageRemove())
    db = interaction.client.async_db["Main"].LockMessage
    await db.replace_one(
        {"Channel": interaction.channel.id, "Guild": interaction.guild.id}, 
        {"Channel": interaction.channel.id, "Guild": interaction.guild.id, "Title": "固定済みメッセージ", "Desc": message.content[:1500], "MessageID": msg.id}, 
        upsert=True
    )
    await interaction.response.send_message(embed=discord.Embed(title="メッセージ固定を有効化しました。", color=discord.Color.green()), ephemeral=True)

@app_commands.context_menu(name="翻訳-Translate")
async def message_translate(interaction: discord.Interaction, message: discord.Message):
    class TranslateMessageCommand(discord.ui.View):
        def __init__(self, message: discord.Message):
            super().__init__(timeout=None)
            self.message = message

        @discord.ui.select(
            cls=discord.ui.Select,
            placeholder="翻訳先を選択",
            options=[
                discord.SelectOption(label="日本語へ (to ja)"),
                discord.SelectOption(label="英語へ (to en)"),
            ]
        )

        async def select(self, interaction: discord.Interaction, select: discord.ui.Select):

            if select.values[0] == "日本語へ (to ja)":
                await interaction.response.defer()

                if not message.content:
                    if not message.embeds:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    
                    if not message.embeds[0].description:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    
                    try:
                        translator = GoogleTranslator(source="auto", target="ja")
                        translated_text = translator.translate(message.embeds[0].description)

                        embed = discord.Embed(
                            title=f"翻訳 (日本語 へ)",
                            description=f"{translated_text}",
                            color=discord.Color.green()
                        )
                        await interaction.followup.send(embed=embed)
                    
                    except Exception as e:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                    return

                try:
                    translator = GoogleTranslator(source="auto", target="ja")
                    translated_text = translator.translate(message.content)

                    embed = discord.Embed(
                        title=f"翻訳 (日本語 へ)",
                        description=f"{translated_text}",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)
                
                except Exception as e:
                    embed = discord.Embed(
                        title="翻訳に失敗しました",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
            elif select.values[0] == "英語へ (to en)":
                await interaction.response.defer()

                if not message.content:
                    if not message.embeds:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    
                    if not message.embeds[0].description:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    
                    try:
                        translator = GoogleTranslator(source="auto", target="en")
                        translated_text = translator.translate(message.embeds[0].description)

                        embed = discord.Embed(
                            title=f"翻訳 (英語 へ)",
                            description=f"{translated_text}",
                            color=discord.Color.green()
                        )
                        await interaction.followup.send(embed=embed)
                    
                    except Exception as e:
                        embed = discord.Embed(
                            title="翻訳に失敗しました",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                    return

                try:
                    translator = GoogleTranslator(source="auto", target="en")
                    translated_text = translator.translate(message.content)

                    embed = discord.Embed(
                        title=f"翻訳 (英語 へ)",
                        description=f"{translated_text}",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)
                
                except Exception as e:
                    embed = discord.Embed(
                        title="翻訳に失敗しました",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)

    await interaction.response.send_message(ephemeral=True, view=TranslateMessageCommand(message), embed=discord.Embed(title="翻訳先を選択してください", description="Please select Language.", color=discord.Color.blue()).set_footer(text=f"mid:{message.id}"))

async def get_user_savedata(client: commands.Bot, user: discord.User):
    db = client.async_db["Main"].LoginData
    try:
        dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
    except:
        return None
    if dbfind is None:
        return None
    return dbfind

@app_commands.context_menu(name="ユーザー情報")
async def user_info(interaction: discord.Interaction, member: discord.Member):
    user = member
    await interaction.response.defer()
    try:
        if interaction.guild is None:
            return await interaction.followup.send(ephemeral=True, content="DMでは使用できません。")
        JST = datetime.timezone(datetime.timedelta(hours=9))
        isguild = None
        isbot = None
        if interaction.guild.get_member(user.id):
            isguild = "います。"
        else:
            isguild = "いません。"
        if user.bot:
            isbot = "はい"
        else:
            isbot = "いいえ"
        permissions = "ユーザー"
        try:
            if interaction.client.get_guild(1323780339285360660).get_role(1325246452829650944) in interaction.client.get_guild(1323780339285360660).get_member(user.id).roles:
                permissions = "モデレーター"
            if user.id == 1335428061541437531:
                permissions = "管理者"
            if user.id == 1346643900395159572:
                permissions = "SharkBot"
        except:
            pass
        
        embed = discord.Embed(title=f"{user.display_name}の情報", color=discord.Color.green())
        embed.add_field(name="基本情報", value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**").add_field(name="サービス情報", value=f"権限: **{permissions}**")
        userdata = await get_user_savedata(interaction.client, user)
        if userdata:
            guild = int(userdata["Guild"])
            logininfo = f"**言語**: {userdata["Lang"]}\n"
            if interaction.client.get_guild(guild):
                gu = interaction.client.get_guild(guild)
                logininfo += f"**最後に認証したサーバーの名前**: {gu.name}\n"
                logininfo += f"**最後に認証したサーバーのid**: {gu.id}"
            embed.add_field(name="ログイン情報", value=logininfo, inline=False)
            pre = userdata["Nitro"]
            if pre == 0:
                embed.add_field(name="Nitro", value="なし", inline=False)
            elif pre == 1:
                embed.add_field(name="Nitro", value="Nitro Classic", inline=False)
            elif pre == 2:
                embed.add_field(name="Nitro", value="Nitro", inline=False)
            elif pre == 3:
                embed.add_field(name="Nitro", value="Nitro Basic", inline=False)
        if user.avatar:
            await interaction.followup.send(embed=embed.set_thumbnail(url=user.avatar.url))
        else:
            await interaction.followup.send(embed=embed.set_thumbnail(url=user.default_avatar.url))
    except:
        return

async def ban_check_shark(int_: discord.Interaction):
    db = int_.client.async_db["Main"].BlockUser
    try:
        dbfind = await db.find_one({"User": int_.user.id}, {"_id": False})
    except:
        return "いいえ"
    if not dbfind is None:
        return "はい"
    return "いいえ"

def change_bool_to_string(bool_: bool):
    if bool_:
        return "はい"
    return "いいえ"

@app_commands.context_menu(name="警告")
async def warn(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(embed=discord.Embed(title="権限がありません。", color=discord.Color.red()), ephemeral=True)
    if member.bot:
        return await interaction.response.send_message(ephemeral=True, content="Botは警告できません。")
    class send(discord.ui.Modal):
        def __init__(self) -> None:
            super().__init__(title="警告をする", timeout=None)
            self.reason = discord.ui.TextInput(label="理由",placeholder="理由を入力",style=discord.TextStyle.long,required=True)
            self.add_item(self.reason)

        async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.defer()
            try:
                await member.send(embed=discord.Embed(title=f"あなたは`{interaction.guild.name}`で警告されました。", color=discord.Color.yellow()).add_field(name="理由", value=self.reason))
            except:
                pass
            await interaction.followup.send(embed=discord.Embed(title="警告されました。", color=discord.Color.red()).add_field(name="理由", value=self.reason), content=f"{member.mention}")
    await interaction.response.send_modal(send())
        
@app_commands.context_menu(name="権限を見る")
async def permissions_check(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    try:
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
        user_perms = [PERMISSION_TRANSLATIONS.get(perm, perm) for perm, value in member.guild_permissions if value]
        user_perms_str = ", ".join(user_perms)
        avatar = member.avatar.url if member.avatar else member.display_avatar.url
        await interaction.followup.send(embed=discord.Embed(title=f"{member.name}さんの権限", description=user_perms_str, color=discord.Color.green()).set_thumbnail(url=avatar))
    except Exception as e:
        return await interaction.followup.send(embed=discord.Embed(title=f"{member.name}さんの権限", description=f"権限の取得に失敗しました。\n`{e}`", color=discord.Color.red()))

@app_commands.context_menu(name="その他")
async def more_command_member(interaction: discord.Interaction, member: discord.Member):
    class MoreMessageCommand(discord.ui.View):
        def __init__(self, member: discord.Member):
            super().__init__(timeout=None)
            self.member = member

        @discord.ui.select(
            cls=discord.ui.Select,
            placeholder="そのメンバーに対して使用するコマンド",
            options=[
                discord.SelectOption(label="ニックネーム編集"),
                discord.SelectOption(label="ニックネームリセット"),
            ]
        )

        async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
            if select.values[0] == "ニックネーム編集":
                if not interaction.user.guild_permissions.manage_nicknames:
                    return await interaction.response.send_message(embed=discord.Embed(title="権限がありません。", color=discord.Color.red()), ephemeral=True)
                class EditMember(discord.ui.Modal, title='ニックネームを編集'):
                    m = discord.ui.TextInput(
                        label='名前を入力',
                        placeholder=f'{self.member.display_name}',
                        style=discord.TextStyle.short,
                        required=True
                    )

                    mid = discord.ui.TextInput(
                        label='メンバーid',
                        style=discord.TextStyle.short,
                        default=f"{self.member.id}",
                        required=True
                    )

                    async def on_submit(self, interaction: discord.Interaction):
                        await interaction.response.defer()
                        try:
                            mid = interaction.guild.get_member(int(self.mid.value))
                            await mid.edit(nick=self.m.value)
                            await interaction.followup.send(embed=discord.Embed(title="ニックネームを編集しました。", color=discord.Color.green()))
                        except:
                            return await interaction.followup.send(embed=discord.Embed(title="ニックネームを編集できませんでした。", color=discord.Color.red()))
                await interaction.response.send_modal(EditMember())
            elif select.values[0] == "ニックネームリセット":
                if not interaction.user.guild_permissions.manage_nicknames:
                    return await interaction.response.send_message(embed=discord.Embed(title="権限がありません。", color=discord.Color.red()), ephemeral=True)
                await interaction.response.defer()
                try:
                    await self.member.edit(nick=None)
                    await interaction.followup.send(embed=discord.Embed(title="ニックネームをリセットしました。", color=discord.Color.green()))
                except:
                    return await interaction.followup.send(embed=discord.Embed(title="ニックネームを編集できませんでした。", color=discord.Color.red()))
    await interaction.response.send_message(ephemeral=True, view=MoreMessageCommand(member), embed=discord.Embed(title="その他のコンテキストメニュー", description="メンバー版", color=discord.Color.blue()).set_footer(text=f"mid:{member.id}"))

async def setup(bot):
    await bot.add_cog(InfoCog(bot))

    bot.tree.add_command(user_info)
    bot.tree.add_command(message_translate)
    bot.tree.add_command(message_pin)
    bot.tree.add_command(miq_command)
    bot.tree.add_command(more_command)
    bot.tree.add_command(warn)
    bot.tree.add_command(permissions_check)
    bot.tree.add_command(more_command_member)