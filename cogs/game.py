from discord.ext import commands
import discord
import traceback
import sys
import requests
import logging
import random
import time
import re
import io
from functools import partial
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
import datetime
import asyncio
import aiohttp
import json
from discord import Webhook
from bs4 import BeautifulSoup
from mcstatus import JavaServer
import base64
import aiofiles
from akinator_python import Akinator

PLAYER_X = "❌"
PLAYER_O = "⭕"
EMPTY = "⬜"

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=EMPTY, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if view.current_player != interaction.user:
            await interaction.response.send_message("あなたの番ではありません！", ephemeral=True)
            return

        if self.label != EMPTY:
            await interaction.response.send_message("ここはすでに選ばれています。", ephemeral=True)
            return

        self.label = PLAYER_X if view.turn % 2 == 0 else PLAYER_O
        self.disabled = True
        await interaction.response.edit_message(view=view)

        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.followup.send(f"{winner} の勝ち！")
            await interaction.message.edit(view=None, embed=discord.Embed(title="対戦が終了しました。", color=discord.Color.green()))
        elif view.turn == 8:
            for child in view.children:
                child.disabled = True
            await interaction.followup.send("引き分けです！")
            await interaction.message.edit(view=None, embed=discord.Embed(title="対戦が終了しました。", color=discord.Color.green()))
        else:
            view.turn += 1
            view.current_player = view.players[view.turn % 2]
            mark = PLAYER_X if view.turn % 2 == 0 else PLAYER_O
            await interaction.message.edit(embed=discord.Embed(title="対戦中です", description=f"{view.current_player.mention} の番です（{mark}）", color=discord.Color.blue()), view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=None)
        self.players = [player1, player2]
        self.current_player = player1
        self.turn = 0

        self.board = [[None for _ in range(3)] for _ in range(3)]

        for y in range(3):
            for x in range(3):
                button = TicTacToeButton(x, y)
                self.add_item(button)

    def check_winner(self):
        grid = [[b.label for b in self.children[y * 3:(y + 1) * 3]] for y in range(3)]
        lines = (
            grid[0], grid[1], grid[2],

            [grid[0][0], grid[1][0], grid[2][0]],
            [grid[0][1], grid[1][1], grid[2][1]],
            [grid[0][2], grid[1][2], grid[2][2]],

            [grid[0][0], grid[1][1], grid[2][2]],
            [grid[0][2], grid[1][1], grid[2][0]],
        )
        for line in lines:
            if line[0] != EMPTY and line[0] == line[1] == line[2]:
                return line[0]
        return None

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.imgurclientid = self.tkj["ImgurClientID"]
        print(f"init -> GameCog")

    @commands.hybrid_group(name="game", description="モンハンワールドのモンスターを取得するよ", fallback="monster")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def game_monster(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="現在製作中です。", color=discord.Color.green()))

    @game_monster.command(name="minecraft", description="Minecraftのユーザーの情報を取得するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def minecraft(self, ctx: commands.Context, ユーザーネーム: str):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.mojang.com/users/profiles/minecraft/{ユーザーネーム}') as response:
                    j = json.loads(await response.text())
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'https://api.minetools.eu/profile/{j["id"]}') as rs:
                            jj = json.loads(await rs.text())
                            await ctx.reply(embed=discord.Embed(title="Minecraftのユーザー情報", description=f"ID: {j["id"]}\nName: {j["name"]}", color=discord.Color.green()).set_thumbnail(url=f"{jj["decoded"]["textures"]["SKIN"]["url"]}").set_image(url=f"https://mc-heads.net/body/{ユーザーネーム}/200"))
        except:
            return await ctx.reply(embed=discord.Embed(title="ユーザー情報の取得に失敗しました。", color=discord.Color.red()))

    @game_monster.command(name="dynmap", description="Dynmapを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def dynmap(self, ctx: commands.Context, dynmapのurl: str):
        await ctx.defer()
        connector = ProxyConnector.from_url('socks5://127.0.0.1:9150')
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(f'https://{dynmapのurl}/up/world/world/') as response:
                    js = json.loads(await response.text())
                    embed = discord.Embed(title="Dynmapの情報", color=discord.Color.green())
                    servertime = (
                                datetime.datetime.min
                                +datetime.timedelta(seconds=(js['servertime']/1000+6)*3600)
                                ).strftime('%H:%M:%S')
                    embed.add_field(name="サーバー内時刻", value=servertime, inline=False)
                    if len(js["players"]) == 0:
                        embed.add_field(name="プレイヤー情報", value="参加しているプレイヤーはいません。", inline=False)
                    else:
                        embed.add_field(name="プレイヤー情報", value="=================", inline=False)
                    players = js["players"]
                    for p in players:
                        embed.add_field(name=f"{p["name"]}", value=f"X座標: {p["x"]}\nY座標: {p["y"]}\nZ座標: {p["z"]}\bHP: {p["health"]}\nワールド: {p["world"]}", inline=False)
                    await ctx.reply(embed=embed)
            except Exception as e:
                return await ctx.reply(embed=discord.Embed(title="取得に失敗しました。", color=discord.Color.red(), description=f"{e}"))

    @game_monster.command(name="java-server", description="Minecraftサーバー(Java)の情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def java_server(self, ctx: commands.Context, アドレス: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'https://api.mcsrvstat.us/3/{アドレス}') as response:
                    if response.status == 200:
                        j = json.loads(await response.text())
                        embed = discord.Embed(title=f"「{j['motd']['clean']}」\nの情報", color=discord.Color.green())
                        pl = j.get('players', {}).get('list', [])  # プレイヤーリストが存在しない場合のエラーを回避
                        embed.add_field(name="参加人数", value=f'{j["players"]["online"]}人')
                        embed.add_field(name="最大参加人数", value=f'{j["players"]["max"]}人')
                        if pl:
                            embed.add_field(name="参加者", value=f"{'\n'.join([f'{p['name']}' for p in pl])}", inline=False)
                        else:
                            embed.add_field(name="参加者", value="現在オンラインのプレイヤーはいません", inline=False)

                        # アイコンが存在する場合のみ処理を行う
                        if "icon" in j:
                            try:
                                i = base64.b64decode(j["icon"].split(';base64,')[1]) # base64データを抽出
                                ii = io.BytesIO(i) # BytesIOオブジェクトを直接作成
                                embed.set_thumbnail(url="attachment://f.png") # サムネイルを設定
                                await ctx.reply(embed=embed, file=discord.File(ii, "f.png"))
                            except Exception as e:
                                print(f"アイコン処理エラー: {e}")
                                await ctx.reply(embed=embed, content="サーバーアイコンの読み込みに失敗しました。")
                        else:
                            await ctx.reply(embed=embed) # アイコンがない場合はembedのみ送信

                    else:
                        await ctx.reply(f"サーバー情報を取得できませんでした。ステータスコード: {response.status}")
            except aiohttp.ClientError as e:
                await ctx.reply(f"サーバーへの接続に失敗しました: {e}")
            except json.JSONDecodeError as e:
                await ctx.reply(f"JSONデータの解析に失敗しました: {e}")
            except Exception as e:
                await ctx.reply(f"予期せぬエラーが発生しました: {e}")

    @game_monster.command(name="amongus-announce", description="AmongUsのアナウンスを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def game_amongus_announce(self, ctx: commands.Context):
        await ctx.defer()
        params = {
            'lang': "11",
            'id': "-1"
        }

        headers = {
            'User-Agent': "UnityPlayer/2020.3.45f1 (UnityWebRequest/1.0, libcurl/7.84.0-DEV)",
            'Accept-Encoding': "deflate, gzip",
            'X-Platform': "Android",
            'X-Unity-Version': "2020.3.45f1"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://backend.innersloth.com/api/announcements', params=params, headers=headers) as response:
                js = await response.json()
                await ctx.reply(embed=discord.Embed(title="AmongUsのニュース", description=f"{js["data"]["attributes"]["announcements"][0]["text"]}", color=discord.Color.blue()))

    def all_same(self, lst):
        return all(x == lst[0] for x in lst) if lst else True

    async def remove_sharkpoint(self, ctx: commands.Context, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": ctx.author.id})
        if user_data:
            if coin > user_data.get("count", 0):
                return False
            await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": -coin}})
            return True
        else:
            return False
        
    async def horihori_go(self, ctx: commands.Context, count: int):
        db = self.bot.async_db["Main"].HoriHoriGame
        user_data = await db.find_one({"_id": ctx.author.id})
        if user_data:
            await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": count}})
            return True
        else:
            await db.replace_one(
                {"_id": ctx.author.id, "count": count}, 
                {"_id": ctx.author.id, "count": count}, 
                upsert=True
            )
            return True
        
    async def horihori_get(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].HoriHoriGame
        try:
            dbfind = await db.find_one({"_id": ctx.author.id}, {"_id": False})
        except:
            return 0
        if not dbfind is None:
            return dbfind.get("count", 0)
        return 0
        
    async def horihori_reset(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].HoriHoriGame
        await db.replace_one(
            {"_id": ctx.author.id}, 
            {"_id": ctx.author.id, "count": 0}, 
            upsert=True
        )
        return True

    async def add_pfact_horihori(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].SharkBotPointFactory
        user_data = await db.find_one({"_id": ctx.author.id})
        if user_data:
            await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": 1}})
            return True
        else:
            await db.insert_one({"_id": ctx.author.id, "count": 1})
            return True

    @game_monster.command(name="horihori", description="採掘ゲームをプレイします。1ポイント必要です。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def horihori_game(self, ctx: commands.Context, ポイント: int):
        if ctx.interaction:
            await ctx.interaction.response.defer()
        if abs(ポイント) == 0:
            return await ctx.reply(embed=discord.Embed(title="ポイントが足りないよ！", description="0ポイントではできないヨ！", color=discord.Color.red()))
        ram = random.randint(0, 2)
        check = await self.remove_sharkpoint(ctx, abs(ポイント))
        hg = await self.horihori_get(ctx)
        msg = await ctx.send(embed=discord.Embed(title="採掘中・・", description="```" + "_" * hg + "->" + "```", color=discord.Color.blue()))
        await asyncio.sleep(2)
        await self.horihori_go(ctx, abs(ポイント)*ram)
        hg_af = await self.horihori_get(ctx)
        if hg_af > 100:
            await self.horihori_reset(ctx)
            await self.add_pfact_horihori(ctx)
            return await msg.edit(embed=discord.Embed(title="採掘しました！", description="全部採掘しました！\nポイント工場を入手しました。\n\n```" + "_" * hg_af + "->🏭" + "```", color=discord.Color.green()))
        await msg.edit(embed=discord.Embed(title="採掘しました！", description="```" + "_" * hg_af + "->" + "```", color=discord.Color.green()))

    @game_monster.command(name="slot", description="ポイントを使ってスロットゲームで遊びます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def slot_game(self, ctx: commands.Context, ポイント: int):
        if ctx.interaction:
            await ctx.interaction.response.defer()

        slot_item = ["🍎", "🍌", "🍇", "🍊", "🍒"]
        check = await self.remove_sharkpoint(ctx, abs(ポイント))
        if not check:
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=discord.Embed(title="ポイントが足りません。", color=discord.Color.red()))
            else:
                await ctx.send(embed=discord.Embed(title="ポイントが足りません。", color=discord.Color.red()))
        msg = await ctx.send(embed=discord.Embed(title="スロット", description="🍎 🍎 🍎", color=discord.Color.blue()))

        now_item = []
        for _ in range(3):
            await asyncio.sleep(1)
            now_item = random.choices(slot_item, k=3)
            await msg.edit(embed=discord.Embed(title="スロット", description=" ".join(now_item), color=discord.Color.blue()))

        result_embed = discord.Embed(
            title="結果", 
            description="あたり" if len(set(now_item)) == 1 else "はずれ",
            color=discord.Color.green() if len(set(now_item)) == 1 else discord.Color.red()
        )

        async def add_sharkpoint(ctx: commands.Context, coin: int):
            db = self.bot.async_db["Main"].SharkBotInstallPoint
            user_data = await db.find_one({"_id": ctx.author.id})
            if user_data:
                await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": coin}})
                return True
            else:
                await db.insert_one({"_id": ctx.author.id, "count": coin})
                return True

        ch = "あたり" if len(set(now_item)) == 1 else "はずれ"

        if ch == "あたり":
            await add_sharkpoint(ctx, ポイント*2)

        if ctx.interaction:
            await ctx.interaction.followup.send(embed=result_embed)
        else:
            await ctx.send(embed=result_embed)

    @game_monster.command(name="tictactoe", description="OXゲームをします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tictactoe(self, ctx: commands.Context, 対戦相手: discord.Member):
        if 対戦相手.bot:
            await ctx.reply("Botとは対戦できません。", ephemeral=True)
            return

        view = TicTacToeView(ctx.author, 対戦相手)

        await ctx.channel.send(view=view, embed=discord.Embed(title="対戦中です", color=discord.Color.blue(), description=f"{ctx.author.mention} の番です"))

        if ctx.interaction:
            await ctx.reply(ephemeral=True, content="対戦が開始されました。")

    @game_monster.command(name="giveaway", description="ポイントを使ってスロットゲームで遊びます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def give_a_way(self, ctx: commands.Context, 時間: str, 商品名: str):
        await ctx.defer(ephemeral=True)
        def parse_time(timestr):
            time_regex = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")
            match = time_regex.fullmatch(timestr.lower())
            if not match:
                return None
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        seconds = parse_time(時間)
        if seconds is None or seconds <= 0:
            await ctx.send("時間の形式が正しくありません。例: `10m`, `1h30m`, `45s`")
            return

        embed = discord.Embed(title="🎉 Giveaway! 🎉",
                            description=f"{商品名}\n\nリアクションで参加！\n終了まで: {時間}",
                            color=discord.Color.gold())
        embed.set_footer(text="終了までお待ちください...")

        message = await ctx.channel.send(embed=embed)
        await message.add_reaction("🎉")

        await ctx.reply("Give a wayを作成しました。", ephemeral=True)

        await asyncio.sleep(seconds)

        message = await ctx.channel.fetch_message(message.id)
        users = []
        async for user in message.reactions[0].users():
            if not user.bot:
                users.append(user)

        if not users:
            await ctx.send("参加者がいませんでした。")
        else:
            winner = random.choice(users)
            await ctx.send(f"🎉 おめでとう！{winner.mention} が **{商品名}** に当選しました！")

async def setup(bot):
    await bot.add_cog(GameCog(bot))