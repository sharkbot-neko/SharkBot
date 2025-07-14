from discord.ext import commands, tasks
import discord
import traceback
import sys
from unbelievaboat import Client
import logging
import time
import aiofiles
import asyncio
import aiohttp
from discord import app_commands
import aiosqlite
import ssl
import json
import re
import random
import string
from itertools import islice

from collections import Counter

def compress_list(lst):
    count = Counter(lst)
    return [f"{item} ×{count[item]}" if count[item] > 1 else item for item in count]


def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)

def chunk_list_iter(lst, size):
    it = iter(lst)
    return iter(lambda: list(islice(it, size)), [])

class Paginator(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.index = 0

    async def update_message(self, interaction):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.next_page.disabled = False
        if self.index == 0:
            self.previous_page.disabled = True
        await self.update_message(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.previous_page.disabled = False
        if self.index == len(self.embeds) - 1:
            self.next_page.disabled = True
        await self.update_message(interaction)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.gray)
    async def close_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="ページを閉じました。", embed=None, view=None)

STOCKS = {"AAPL": 150, "TSLA": 700, "GOOGL": 2800}

COOLDOWN_TIME_WORK = 5
cooldown_work_time = {}
cooldown_work_crime = {}
cooldown_work_daily = {}

def draw_card():
    cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    return random.choice(cards)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def calculate_score(hand):
    values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11}
    score = sum(values[card] for card in hand)
    if score > 21 and "A" in hand:
        score -= 10  # Aを1として扱う
    return score

class BlackjackView(discord.ui.View):
    def __init__(self, player_hand, dealer_hand):
        super().__init__()
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(draw_card())
        player_score = calculate_score(self.player_hand)
        
        if player_score > 21:
            await interaction.response.edit_message(content=f"あなたの手札: {self.player_hand} (Score: {player_score})\nバーストしました！ディーラーの勝ち！", view=None)
        else:
            await interaction.response.edit_message(content=f"あなたの手札: {self.player_hand} (Score: {player_score})\nディーラーの1枚目: {self.dealer_hand[0]}", view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_score = calculate_score(self.player_hand)
        dealer_score = calculate_score(self.dealer_hand)
        
        while dealer_score < 17:
            self.dealer_hand.append(draw_card())
            dealer_score = calculate_score(self.dealer_hand)
        
        result = ""
        if dealer_score > 21 or player_score > dealer_score:
            result = "あなたの勝ち！"
        elif player_score < dealer_score:
            result = "ディーラーの勝ち！"
        else:
            result = "引き分け！"
        
        await interaction.response.edit_message(content=f"あなたの手札: {self.player_hand} (Score: {player_score})\nディーラーの手札: {self.dealer_hand} (Score: {dealer_score})\n{result}", view=None)

user_last_message_time_work = {}
user_last_message_time_resale = {}

class MoneyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.mt = self.tkj["MoneyBotToken"]
        print(f"init -> MoneyCog")

    async def get_ban_count(self, user: discord.User):
        try:
            db = self.bot.async_db["Main"].BANRanking
            try:
                dbfind = await db.find_one({"_id": user.id}, {"_id": False})
                return dbfind["ban_count"]
            except Exception as e:
                return 0
        except:
            return 0

    async def get_delete_count(self, user: discord.User):
        try:
            db = self.bot.async_db["Main"].MessageDeleteRanking
            try:
                dbfind = await db.find_one({"_id": user.id}, {"_id": False})
                return dbfind["delete_count"]
            except Exception as e:
                return 0
        except:
            return 0

    async def add_money(self, author: discord.User, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": author.id})
        if user_data:
            await db.update_one({"_id": author.id}, {"$inc": {"count": coin}})
            return True
        else:
            await db.insert_one({"_id": author.id, "count": coin})
            return True
        
    async def add_debt(self, author: discord.User, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPointDebt
        user_data = await db.find_one({"_id": author.id})
        if user_data:
            await db.update_one({"_id": author.id}, {"$inc": {"count": coin}})
            return True
        else:
            await db.insert_one({"_id": author.id, "count": coin})
            return True

    async def remove_money(self, author: discord.User, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": author.id})
        if user_data:
            if coin > user_data.get("count", 0):
                return False
            await db.update_one({"_id": author.id}, {"$inc": {"count": -coin}})
            return True
        else:
            return False
        
    async def remove_debt(self, author: discord.User, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPointDebt
        user_data = await db.find_one({"_id": author.id})
        if user_data:
            if coin > user_data.get("count", 0):
                return False
            await db.update_one({"_id": author.id}, {"$inc": {"count": -coin}})
            return True
        else:
            return False

    async def get_money(self, author: discord.User):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        try:
            dbfind = await db.find_one({"_id": author.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        return dbfind.get("count", 0)
    
    async def get_debt(self, author: discord.User):
        db = self.bot.async_db["Main"].SharkBotInstallPointDebt
        try:
            dbfind = await db.find_one({"_id": author.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        return dbfind.get("count", 0)

    async def get_twitter(self, author: discord.User):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://search.yahoo.co.jp/realtime/api/v1/pagination', params={"p": f"{author.display_name}"}, ssl=ssl_context) as response:
                js = await response.json()
                check = len(js["timeline"]["entry"])
                if check == 0:
                    return None
                title = js["timeline"]["entry"][0]["displayText"].replace("\\tSTART\\","").replace("\\tEND\\","")
                return title

    @commands.hybrid_group(name="economy", description="働いて、給料を得ます。", fallback="work")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_work(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        last_message_time = user_last_message_time_work.get(ctx.author.id, 0)
        if current_time - last_message_time < 1800:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 30分に一回働けます。", color=discord.Color.red()), ephemeral=True)
        user_last_message_time_work[ctx.author.id] = current_time
        m = random.randint(1, 3)
        await self.add_money(ctx.author, m)
        us = random.choice(ctx.guild.members)
        hataraku = [f"{us.display_name}のコンビニでバイトをして、", f"{us.display_name}のためにプログラミングをして、", f"{us.display_name}の銀行で働いて、", f"{us.display_name}のパン屋でバイトをし、", f"{us.display_name}のサーバーで運営をし、"]
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 働きました。", description=f"{random.choice(hataraku)}\n{m}ポイントを獲得しました。", color=discord.Color.green()))
        return
    
    @economy_work.command(name="balance", description="残高を取得します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_balance(self, ctx: commands.Context, ユーザー: discord.User = None):
        await ctx.defer()
        if not ユーザー:
            mo = await self.get_money(ctx.author)
            deb = await self.get_debt(ctx.author)
            await ctx.reply(embed=discord.Embed(title=f"<:Success:1362271281302601749> {ctx.author}さんの残高", color=discord.Color.green(), description=f"残高: {mo}ポイント\n借金: {deb}ポイント"))
            return
        else:
            if ユーザー.bot:
                return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> Botはポイントを持てません。", color=discord.Color.red()))
            mo = await self.get_money(ユーザー)
            deb = await self.get_debt(ユーザー)
            await ctx.reply(embed=discord.Embed(title=f"<:Success:1362271281302601749> {ユーザー.name}さんの残高", color=discord.Color.green(), description=f"残高: {mo}ポイント\n借金: {deb}ポイント"))
            return
        
    @economy_work.command(name="pay", description="ポイントを相手に払います。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_pay(self, ctx: commands.Context, ユーザー: discord.User, コイン: int):
        await ctx.defer()
        if ユーザー.bot:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> Botはポイントを持てません。", color=discord.Color.red()))
        if コイン <= 0:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 1コイン以上しか渡せません。", color=discord.Color.red()))
        deb = await self.get_debt(ctx.author)
        if not deb == 0:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 渡すためのお金がありません。", description="借金をしてるのに渡せるわけないよね？ｗｗｗ", color=discord.Color.red()))
        u = await self.remove_money(ctx.author, コイン)
        if not u:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 渡すためのお金がありません。", color=discord.Color.red()))
        await self.add_money(ユーザー, コイン)
        await ctx.reply(embed=discord.Embed(title=f"<:Success:1362271281302601749> {ユーザー.name}さんにポイントを渡しました。", color=discord.Color.green()))
        return
    
    @economy_work.command(name="crime", description="犯罪をし、お金を得ます。たまに失敗します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_crime(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        last_message_time = cooldown_work_crime.get(ctx.author.id, 0)
        if current_time - last_message_time < 3600:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 一時間に一回犯罪できます。", color=discord.Color.red()), ephemeral=True)
        cooldown_work_crime[ctx.author.id] = current_time
        m = random.randint(1, 5)
        await self.add_money(ctx.author, m)
        hanzai = ["強盗", "サイバー犯罪", "詐欺", "ストーカー"]
        us = random.choice(ctx.guild.members)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 犯罪をしました。", description=f"{us.display_name}に対して{random.choice(hanzai)}をし、\n{m}ポイント得ました。", color=discord.Color.green()))
        return
    
    @economy_work.command(name="daily", description="一日一回お金を得ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_daily(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        last_message_time = cooldown_work_daily.get(ctx.author.id, 0)
        if current_time - last_message_time < 86400:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 一日一回もらえます。", color=discord.Color.red()), ephemeral=True)
        cooldown_work_daily[ctx.author.id] = current_time
        m = random.randint(1, 3)
        await self.add_money(ctx.author, m)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> お金をもらいました。", description=f"{m}ポイント得ました。", color=discord.Color.green()))
        return

    @economy_work.command(name="pray", description="神に祈り、ポイントを得ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_pray(self, ctx: commands.Context):
        await ctx.defer()
        random_word = []
        check = random.randint(0, 10)
        if check == 7:
            tw = await self.get_twitter(ctx.author)
            if tw:
                random_word.append(f"あなたは、Twitterで、\n{tw[:15]}..\nと発言したことで、")
            delete = await self.get_delete_count(ctx.author)
            if not delete == 0:
                random_word.append(f"あなたは、様々なサーバーで、\n合計{delete}回メッセージを削除したことで、")
            random_word.append(f"あなたは、{random.choice(ctx.guild.members).display_name}に食料を与えたため、")
            p = random.randint(1, 10)
            await self.add_money(ctx.author, p)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> お金をもらいました。", description=f"{random.choice(random_word)}\n{p}ポイントをもらいました。", color=discord.Color.green()))
        else:
            tw = await self.get_twitter(ctx.author)
            if tw:
                random_word.append(f"あなたは、Twitterで、\n{tw[:15]}..\nと発言したことが神にばれ、")
            ban = await self.get_ban_count(ctx.author)
            if not ban == 0:
                random_word.append(f"あなたは、様々なサーバーで、\n合計{ban}回BANされていることが神にばれ、")
            delete = await self.get_delete_count(ctx.author)
            if not delete == 0:
                random_word.append(f"あなたは、様々なサーバーで、\n合計{delete}回メッセージを削除していたことが神にばれ、")
            random_word.append(f"あなたは、{random.choice(ctx.guild.members).display_name}に喧嘩をうったことが神にばれ、")
            random_word.append(f"あなたは、{random.choice(["モンハン", "フォートナイト", "Apex", "Minecraft"])}で害悪プレイをしたことが神にばれ、")
            await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> お金をもらえませんでした。", description=f"{random.choice(random_word)}\n何ももらうことができませんでした。。", color=discord.Color.red()))

    @economy_work.command(name="resale", description="転売をして、ポイントを得ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_resale(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        last_message_time = user_last_message_time_resale.get(ctx.author.id, 0)
        if current_time - last_message_time < 1800:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 30分に一回転売できます。", color=discord.Color.red()), ephemeral=True)
        user_last_message_time_resale[ctx.author.id] = current_time
        m = random.randint(1, 5)
        await self.add_money(ctx.author, m)
        us = random.choice(ctx.guild.members)
        tenbai = ["スOッチ2を転売し、", "とあるビデオを転売し、", "アイドルの写真を転売し、", "マスクを転売し、", "お米を大量に転売し、"]
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 転売をしました。", description=f"{random.choice(tenbai)}\n{m}ポイントを獲得しました。", color=discord.Color.green()))
        return

    @economy_work.command(name="job", description="お金がもらえる仕事をします。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_job(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        last_message_time = user_last_message_time_resale.get(ctx.author.id, 0)
        if current_time - last_message_time < 1800:
            return await ctx.reply(embed=discord.Embed(title=f"<:Error:1362271424227709028> 30分に一回仕事できます。", color=discord.Color.red()), ephemeral=True)
        user_last_message_time_resale[ctx.author.id] = current_time
        m = random.randint(1, 5)
        await self.add_money(ctx.author, m)
        us = random.choice(ctx.guild.members)
        tenbai = [f"{us.display_name}の作ったゲームの\nデバッグのアルバイトをして、", f"{us.display_name}のコンビニでアルバイトをして、", f"{us.display_name}のペットショップでアルバイトをして、", f"{us.display_name}の会社で働いて、", f"{us.display_name}の銀行で働いて、"]
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 仕事をしました。", description=f"{random.choice(tenbai)}\n{m}ポイントを獲得しました。", color=discord.Color.green()))
        return

    @economy_work.command(name="debt", description="借金をします。返す時は、2倍の金額を払う必要があります。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_debt(self, ctx: commands.Context, ポイント: int):
        await ctx.defer()
        MAX_DEBT = 1000

        if ポイント <= 0:
            return await ctx.reply(embed=discord.Embed(
                title="<:Error:1362271424227709028> 借りる金額は1ポイント以上である必要があります。",
                color=discord.Color.red()
            ))

        current_debt = await self.get_debt(ctx.author)
        
        if current_debt + ポイント * 2 > MAX_DEBT:
            return await ctx.reply(embed=discord.Embed(
                title="<:Error:1362271424227709028> 合計借金額が上限を超えています。",
                description=f"現在の借金: {current_debt}ポイント\n最大: {MAX_DEBT}ポイント",
                color=discord.Color.red()
            ))

        await self.add_debt(ctx.author, ポイント * 2)
        await self.add_money(ctx.author, ポイント)
        return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 借金をしました。", description=f"{ポイント*2}ポイントを支払う必要があります。", color=discord.Color.green()))
    
    @economy_work.command(name="black-debt", description="闇金から借金をします。返す時は、10倍の金額を払う必要があります。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_debt_black(self, ctx: commands.Context, ポイント: int):
        await ctx.defer()
        MAX_DEBT = 1000

        if ポイント <= 0:
            return await ctx.reply(embed=discord.Embed(
                title="<:Error:1362271424227709028> 借りる金額は1ポイント以上である必要があります。",
                color=discord.Color.red()
            ))

        current_debt = await self.get_debt(ctx.author)
        
        if current_debt + ポイント * 10 > MAX_DEBT:
            return await ctx.reply(embed=discord.Embed(
                title="<:Error:1362271424227709028> 合計借金額が上限を超えています。",
                description=f"現在の借金: {current_debt}ポイント\n最大: {MAX_DEBT}ポイント",
                color=discord.Color.red()
            ))
        await self.add_debt(ctx.author, ポイント * 10)
        await self.add_money(ctx.author, ポイント)
        return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 借金をしました。", description=f"{ポイント*10}ポイントを支払う必要があります。", color=discord.Color.green()))
    
    @economy_work.command(name="repay", description="借金を返済します。返済額以上を入れると、無駄になります。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def economy_debt_repay(self, ctx: commands.Context, ポイント: int):
        await ctx.defer()
        u = await self.remove_money(ctx.author, ポイント)
        if not u:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> お金が足りません。", color=discord.Color.red()))
        await self.remove_debt(ctx.author, ポイント)
        return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 借金を返済しました。", color=discord.Color.green()))

    """
    async def check_mode_money(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].ServerMode
        profile = await db.find_one({
            "Guild": ctx.guild.id
        })
        if profile is None:
            return "shark"
        if profile["Mode"] == "unb":
            return "unb"
        else:
            return "shark"
    
    @commands.hybrid_group(name="money", description="サーバー内通貨を作成します。", fallback="make")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 300, type=commands.BucketType.guild)
    async def money_make(self, ctx: commands.Context, 通貨名: str):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoney
        try:
            profile = await db.find_one({
                "Guild": ctx.guild.id
            })
            if profile is None:
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": 0, "CoinName": 通貨名}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="通貨を作成しました。", description=f"名前: {通貨名}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title="すでに経済が存在します。", color=discord.Color.red()))
        except:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": 0, "CoinName": 通貨名}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="通貨を作成しました。", description=f"名前: {通貨名}", color=discord.Color.green()))

    @money_make.command(name="mode", description="経済のモードを切り替えます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    @app_commands.choices(設定=[
        app_commands.Choice(name='Shark経済',value="shark"),
        app_commands.Choice(name='Unb経済 ベータ版',value="unb"),
    ])
    async def money_mode(self, ctx: commands.Context, 設定: app_commands.Choice[str]):
        await ctx.defer()
        if 設定.value == "shark":
            db = self.bot.async_db["Main"].ServerMode
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Mode": "shark"}, 
                upsert=True
            )
            db = self.bot.async_db["Main"].ServerMoney
            await db.delete_many({"Guild": ctx.guild.id})
            await ctx.reply(embed=discord.Embed(title="経済モードをSharkに切り替えました。", color=discord.Color.blue()))
        if 設定.value == "unb":
            db = self.bot.async_db["Main"].ServerMode
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Mode": "unb"}, 
                upsert=True
            )
            db = self.bot.async_db["Main"].ServerMoney
            await db.delete_many({"Guild": ctx.guild.id})
            await ctx.reply(embed=discord.Embed(title="経済モードをUnbに切り替えました。", color=discord.Color.blue()))

    async def add_money_unb(self, ctx: commands.Context, お金: int):
        client = Client(self.mt)
        try:
            guild = await client.get_guild(ctx.guild.id)
            user = await guild.get_user_balance(ctx.author.id)
            await user.set(cash=お金 + user.cash)
            return True
        except:
            await ctx.reply(embed=discord.Embed(title="これを認証してください。", description="https://unbelievaboat.com/applications/authorize?app_id=1351137174568960048", color=discord.Color.red()))
            return False
        
    async def get_money_unb(self, ctx: commands.Context):
        client = Client(self.mt)
        try:
            guild = await client.get_guild(ctx.guild.id)
            user = await guild.get_user_balance(ctx.author.id)
            return user
        except:
            await ctx.reply(embed=discord.Embed(title="これを認証してください。", description="https://unbelievaboat.com/applications/authorize?app_id=1351137174568960048", color=discord.Color.red()))
            return False

    @money_make.command(name="work", description="働いて、サーバー内通貨を取得します。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    async def money_work(self, ctx: commands.Context):
        await ctx.defer()

        current_time = time.time()
        last_message_time = cooldown_work_time.get(ctx.author.id, 0)
        if current_time - last_message_time < 1800:
            return await ctx.reply("今はまだ稼げません。\nしばらく待ってください。")
        cooldown_work_time[ctx.author.id] = current_time
        
        db = self.bot.async_db["Main"].ServerMoney
        wm = random.randint(700, 3000)
        try:
            profile = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if profile is None:
                tname = await db.find_one({
                    "Guild": ctx.guild.id
                })
                if tname is None:
                    unb_add = await self.add_money_unb(ctx, wm)
                    if unb_add:
                        return await ctx.reply(embed=discord.Embed(title=f"お金を稼ぎました。", description=f"Unbに追加しました。", color=discord.Color.green()))
                    return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": wm, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return await ctx.reply(embed=discord.Embed(title="お金を稼ぎました。", description=f"稼いだ額: {wm}{tname["CoinName"]}\n現在何{tname["CoinName"]}か: {wm}", color=discord.Color.green()))
            else:
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": wm + profile.get("Money", 0), "CoinName": profile["CoinName"]}, 
                    upsert=True
                )
                return await ctx.reply(embed=discord.Embed(title="お金を稼ぎました。", description=f"稼いだ額: {wm}{profile["CoinName"]}\n現在何{profile["CoinName"]}か: {wm + profile.get("Money", 0)}{profile["CoinName"]}", color=discord.Color.green()))
        except Exception as e:
            unb_add = await self.add_money_unb(ctx, wm)
            if unb_add:
                return await ctx.reply(embed=discord.Embed(title=f"お金を稼ぎました。", description=f"Unbに追加しました。", color=discord.Color.green()))
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))

    @money_make.command(name="money", description="お金を見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_money(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                unb_money = await self.get_money_unb(ctx)
                if unb_money:
                    return await ctx.reply(embed=discord.Embed(title=f"現在のお金", color=discord.Color.green()).add_field(name="手持ち", value=str(unb_money.cash)).add_field(name="銀行", value=str(unb_money.bank)).add_field(name="合計", value=str(unb_money.total)))
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="現在のお金", description=f"{money["Money"]}{money["CoinName"]}", color=discord.Color.green()))
        except:
            unb_money = await self.get_money_unb(ctx)
            if unb_money:
                return await ctx.reply(embed=discord.Embed(title=f"現在のお金", color=discord.Color.green()).add_field(name="手持ち", value=str(unb_money.cash)).add_field(name="銀行", value=str(unb_money.bank)).add_field(name="合計", value=str(unb_money.total)))
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        
    @money_make.command(name="coin", description="お金の名前を見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_coin(self, ctx: commands.Context):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id,
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            await ctx.reply(embed=discord.Embed(title="お金の名前", description=f"{money["CoinName"]}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))

    @money_make.command(name="convert", description="unbelievaboatにお金を変換します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_convert(self, ctx: commands.Context, お金: int):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金を持っていません。", color=discord.Color.red()))
            if money["Money"] < お金:
                return await ctx.reply(embed=discord.Embed(title=f"お金が足りません。", color=discord.Color.red()))
            client = Client(self.mt)
            try:
                guild = await client.get_guild(ctx.guild.id)
                user = await guild.get_user_balance(ctx.author.id)
                await user.set(bank=お金 + user.bank)
            except:
                return await ctx.reply(embed=discord.Embed(title="まずこれを認証してください。", description="https://unbelievaboat.com/applications/authorize?app_id=1351137174568960048", color=discord.Color.red()))
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": money["Money"] - お金, "CoinName": money["CoinName"]}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="お金を変換しました。", description=f"{お金}{money["CoinName"]}\n-> {お金}コイン", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))

    @money_make.command(name="item", description="購入したアイテムを表示します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop_item(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        try:
            mdb = self.bot.async_db["Main"].ServerMoneyItems
            money = await mdb.find_one({
                "User": ユーザー.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはアイテムを持っていません。", color=discord.Color.red()))
            txt = ""
            async for s in mdb.find(filter={'User': ユーザー.id}):
                txt += f"{s["ItemName"]}\n"
            ls = compress_list(txt.split("\n"))
            chunks = chunk_list_iter(ls, 10)
            embeds = []
            for i, chunk in enumerate(chunks, 1):
                embeds.append(discord.Embed(title=f"ページ{i}", description=f"\n".join(chunk), color=discord.Color.blue()))
        except:
            return
        view = Paginator(embeds)
        await ctx.reply(embed=embeds[0], view=view)

    async def add_item(self, ctx: commands.Context, アイテム名: str, 値段: int):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        await idb.replace_one(
            {"User": ctx.author.id, "ItemName": アイテム名, "ID": randomname(5)}, 
            {"User": ctx.author.id, "Money": 値段, "ItemName": アイテム名, "ID": randomname(5)}, 
            upsert=True
        )

    @money_make.command(name="buy", description="ショップからかいます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop_buy(self, ctx: commands.Context, アイテム名: str):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            usermoney = await mdb.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if usermoney is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
            tname = await db.find_one({
                "Guild": ctx.guild.id, "Name": アイテム名
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このにショップにそのアイテムがありません。", color=discord.Color.red()))
            if usermoney.get("Money", 0) > tname["Coin"]:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - tname["Coin"], "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                idb = self.bot.async_db["Main"].ServerMoneyItems
                await idb.replace_one(
                    {"User": ctx.author.id, "ItemName": tname["Name"], "ID": randomname(5)}, 
                    {"User": ctx.author.id, "Money": tname["Coin"], "ItemName": tname["Name"], "ID": randomname(5)}, 
                    upsert=True
                )
                shopdb = self.bot.async_db["Main"].ServerMoneyShop
                await shopdb.delete_one(
                    {"Guild": ctx.guild.id, "Name": アイテム名}
                )
                await ctx.reply(embed=discord.Embed(title=f"{tname["Name"]}を購入しました。", description=f"アイテム名: {tname["Name"]}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップがないか、\nそのアイテムがありません。", description=f"{sys.exc_info()}", color=discord.Color.red()))

    @money_make.command(name="shop", description="ショップを見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop(self, ctx: commands.Context):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            txt = ""
            async for s in db.find(filter={'Guild': ctx.guild.id}):
                txt += f"{s["Name"]} - {s["Coin"]}{money["CoinName"]}\n"
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップ", description=txt, color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
        
    @money_make.command(name="shop_add", description="ショップに追加します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def money_shop_add(self, ctx: commands.Context, アイテムの名前: str, 値段: int):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Name": アイテムの名前}, 
                {"Guild": ctx.guild.id, "Name": アイテムの名前, "Coin": 値段}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップに\nアイテムを追加しました。", description=f"アイテム名: {アイテムの名前}\n値段: {値段}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))

    @money_make.command(name="shop_remove", description="ショップから削除します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def money_shop_remove(self, ctx: commands.Context, アイテムの名前: str):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            await db.delete_one(
                {"Guild": ctx.guild.id, "Name": アイテムの名前}
            )
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップから\nアイテムを削除しました。", description=f"アイテム名: {アイテムの名前}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))

    @money_make.command(name="netshop", description="ブラウザ上でアイテムを購入します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_netshop(self, ctx: commands.Context):
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoney
        try:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/shop?id={ctx.guild.id}")

    @money_make.command(name="gift", description="アイテムをプレゼントします。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_gift(self, ctx: commands.Context, ユーザー: discord.User, アイテム名: str):
        db = self.bot.async_db["Main"].ServerMoney
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.replace_one(
            {"User": ユーザー.id, "ItemName": アイテム名, "ID": randomname(5)}, 
            {"User": ユーザー.id, "Money": profile["Money"], "ItemName": アイテム名, "ID": randomname(5)}, 
            upsert=True
        )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        await ctx.reply(embed=discord.Embed(title="アイテムをプレゼントしました。", description=f"{アイテム名}", color=discord.Color.green()))

    async def remove_money_fund(self, ctx: commands.Context, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            return False
        if usermoney.get("Money", 0) > お金:
            await mdb.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - お金, "CoinName": usermoney["CoinName"]}, 
                upsert=True
            )
            return True
        else:
            return False

    async def add_money_fund(self, ctx: commands.Context, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            tname = await mdb.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": お金, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return True
            else:
                return False
        await mdb.replace_one(
            {"Guild": ctx.guild.id, "User": ctx.author.id}, 
            {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] + お金, "CoinName": usermoney["CoinName"]}, 
            upsert=True
        )
        return True
    
    async def add_money_func_pay(self, ctx: commands.Context, user: discord.User, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": user.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            tname = await mdb.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": user.id}, 
                    {"Guild": ctx.guild.id, "User": user.id, "Money": お金, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return True
            else:
                return False
        await mdb.replace_one(
            {"Guild": ctx.guild.id, "User": user.id}, 
            {"Guild": ctx.guild.id, "User": user.id, "Money": usermoney["Money"] + お金, "CoinName": usermoney["CoinName"]}, 
            upsert=True
        )
        return True

    @money_make.command(name="pay", description="お金を送信します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_pay(self, ctx: commands.Context, ユーザー: discord.User, お金: int):
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        await ctx.defer(ephemeral=True)
        await self.remove_money_fund(ctx, お金)
        await self.add_money_func_pay(ctx, ユーザー, お金)
        await ctx.reply(f"{ユーザー.display_name}さんへ送金しました。", ephemeral=True)

    @money_make.command(name="use", description="アイテムを使います。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_use(self, ctx: commands.Context, アイテム名: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        msg = random.choice(["とけた！", "おいしかった！", "捨てた！", "吐いた！", "転売した！", "飲み込んだ！", "飲んだ！"])
        await ctx.reply(embed=discord.Embed(title=f"{アイテム名}を使用しました。", description=f"{msg}", color=discord.Color.green()))

    @money_make.command(name="sell", description="アイテムを売ります。")
    @commands.cooldown(2, 20, type=commands.BucketType.guild)
    async def money_sell(self, ctx: commands.Context, アイテム名: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        db = self.bot.async_db["Main"].ServerMoney
        moneyadd = await db.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if moneyadd is None:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": profile["Money"], "CoinName": tname["CoinName"]}, 
                upsert=True
            )
        else:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": profile["Money"] + moneyadd.get("Money", 0), "CoinName": moneyadd["CoinName"]}, 
                upsert=True
            )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        shopdb = self.bot.async_db["Main"].ServerMoneyShop
        await shopdb.replace_one(
            {"Guild": ctx.guild.id, "Name": アイテム名}, 
            {"Guild": ctx.guild.id, "Name": アイテム名, "Coin": profile["Money"]}, 
            upsert=True
        )
        tname = await db.find_one({
            "Guild": ctx.guild.id
        })
        await ctx.reply(embed=discord.Embed(title=f"アイテムを売りました。", description=f"{アイテム名}\n{profile["Money"]}{tname["CoinName"]}", color=discord.Color.green()))

    @commands.hybrid_group(name="money-game", description="料理をします。", fallback="cooking")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_cooking(self, ctx: commands.Context, 材料: str, 材料2: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": 材料}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": 材料2}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": 材料}
        )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": 材料2}
        )
        itemname = random.choice(["パンケーキ", "クッキー", "餅", "チョコレート", "マシュマロ", "失敗作", "不思議な料理", "パン", "食パン", "タコス🌮", "コインチョコ", "日本陸軍", "日本海軍", "馬刺し", "チョコクッキー", "おにぎり", "ハンバーグ", "ハンバーガー", "溶岩ステーキ"])
        値段 = random.randint(100, 3000)
        await self.add_item(ctx, itemname, 値段)
        await ctx.reply(embed=discord.Embed(title="料理をしました。", description=f"料理名: {itemname}\n値段: {値段}コイン\n材料: {材料} と {材料2}", color=discord.Color.green()))
    
    @money_cooking.command(name="fish", description="魚を釣ります。")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def money_fish(self, ctx: commands.Context):
        fishname = random.choice(["サメ", "Mee6", "ビン", "カン", "サケ", "マグロ", "死骸"])
        値段 = random.randint(100, 2000)
        await self.add_item(ctx, fishname, 値段)
        await ctx.reply(embed=discord.Embed(title=f"魚を釣りました。", description=f"{fishname}が釣れた！\n値段: {値段}コイン", color=discord.Color.green()))

    async def get_coinname_fund(self, ctx: commands.Context):
        mdb = self.bot.async_db["Main"].ServerMoney
        tname = await mdb.find_one({
            "Guild": ctx.guild.id
        })
        if tname is None:
            return None
        return tname["CoinName"]

    @money_cooking.command(name="guess", description="0~5の間で、数字あてゲームをします。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    async def money_guess(self, ctx: commands.Context, お金: int, 数字: int):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
        if usermoney.get("Money", 0) > お金:
            数字s = random.randint(0, 5)
            await mdb.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - お金, "CoinName": usermoney["CoinName"]}, 
                upsert=True
            )
            if 数字s == 数字:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] + お金 * 3 , "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="正解しました。", description=f"{お金}{usermoney["CoinName"]}使用しました。\n{お金*3}{usermoney["CoinName"]}返ってきました。", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title="不正解です。", description=f"{お金}{usermoney["CoinName"]}使用しました。", color=discord.Color.red()))
        else:
            await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))

    @money_cooking.command(name="roulette", description="ルーレットで遊びます。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    @discord.app_commands.choices(
        赤か黒=[
            discord.app_commands.Choice(name="赤", value="red"),
            discord.app_commands.Choice(name="黒", value="black"),
        ]
    )
    async def money_roulette(self, ctx: commands.Context, お金: int, 赤か黒: discord.app_commands.Choice[str]):
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        m = await self.remove_money_fund(ctx, お金)
        cn = await self.get_coinname_fund(ctx)
        rb = random.choice(["r", "b"])
        if m:
            if 赤か黒.name == "赤":
                if rb == "r":
                    await self.add_money_fund(ctx, お金*3)
                    await ctx.reply(embed=discord.Embed(title="当たりました。", color=discord.Color.green(), description=f"{お金}{cn}を使用して、\n{お金*3}{cn}が返ってきました。"))
                else:
                    return await ctx.reply(embed=discord.Embed(title="外れました。", color=discord.Color.red(), description=f"{お金}{cn}を使用しました。"))
            else:
                if rb == "b":
                    await self.add_money_fund(ctx, お金*3)
                    await ctx.reply(embed=discord.Embed(title="当たりました。", color=discord.Color.green(), description=f"{お金}{cn}を使用して、\n{お金*3}{cn}が返ってきました。"))
                    return
                else:
                    return await ctx.reply(embed=discord.Embed(title="外れました。", color=discord.Color.red(), description=f"{お金}{cn}を使用しました。"))
        else:
            return await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))

    @money_cooking.command(name="blackjack", description="ブラックジャックをします。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    async def money_blackhack(self, ctx: commands.Context):
        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card(), draw_card()]
        view = BlackjackView(player_hand, dealer_hand)
        await ctx.reply(f"あなたの手札: {player_hand}\nディーラーの1枚目: {dealer_hand[0]}", view=view)

    @money_cooking.command(name="amazon", description="ほかの鯖から10倍の価格で取り寄せます")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def money_amazon(self, ctx: commands.Context, アイテム名: str):
        await ctx.defer()
        check_mode = await self.check_mode_money(ctx)
        if check_mode == "unb":
            return await ctx.reply(embed=discord.Embed(title="Unbモードのため使用できません。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            usermoney = await mdb.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if usermoney is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
            tname = await db.find_one({
                "Name": アイテム名
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"どこのショップにもそのアイテムがありません。", color=discord.Color.red()))
            if usermoney.get("Money", 0) > tname["Coin"] * 10:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - tname["Coin"] * 10, "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                await self.add_item(ctx, アイテム名, tname["Coin"] * 10)
                await ctx.reply(embed=discord.Embed(title=f"{tname["Name"]}を購入しました。", description=f"アイテム名: {tname["Name"]}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title=f"お金がありません。", description=f"{tname["Coin"] * 10}{usermoney["CoinName"]}かかります。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップがないか、\nそのアイテムがありません。", description=f"{sys.exc_info()}", color=discord.Color.red()))
    """
    
async def setup(bot):
    await bot.add_cog(MoneyCog(bot))