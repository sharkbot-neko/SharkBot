from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import json
from unbelievaboat import Client
import asyncio

class UpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.mt = self.tkj["MoneyBotToken"]
        print(f"init -> UpCog")

    async def add_money(self, message: discord.Message):
        db = self.bot.async_db["Main"].BumpUpEconomy
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        if dbfind.get("Money", 0) == 0:
            return
        try:
            client = Client(self.mt)
            guild = await client.get_guild(message.guild.id)
            user = await guild.get_user_balance(message.interaction_metadata.user.id)
            await user.set(cash=dbfind.get("Money", 0) + user.cash)

            await message.channel.send(embed=discord.Embed(title="Up・Bumpなどをしたため、給料がもらえました。", description=f"{dbfind.get("Money", 0)}コインです。", color=discord.Color.pink()))
        except:
            return await message.channel.send(embed=discord.Embed(title="追加に失敗しました。", description="以下を管理者権限を持っている人に\n認証してもらってください。\nhttps://unbelievaboat.com/applications/authorize?app_id=1326818885663592015", color=discord.Color.yellow()))

    async def mention_get(self, message: discord.Message):
        db = self.bot.async_db["Main"].BumpUpMention
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return "メンションするロールがありません。"
        if dbfind is None:
            return "メンションするロールがありません。"
        
        try:

            role = message.guild.get_role(dbfind.get("Role", None))
            return role.mention
        except:
            return "メンションするロールがありません。"

    @commands.Cog.listener("on_message")
    async def on_message_up_dicoall(self, message: discord.Message):
        if message.author.id == 903541413298450462:
            try:
                if "残りました。" in message.content:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.channel.send(embed=discord.Embed(title="Upに失敗しました。", description="しばらく待ってから、\n</up:935190259111706754> をお願いします。", color=discord.Color.red()))
            except:
                return
            try:
                if "サーバーは上部に表示されます。" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(embed=discord.Embed(title="Upを検知しました。", description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()))
                    await self.add_money(message)
                    await asyncio.sleep(3600)
                    await message.channel.send(embed=discord.Embed(title="DicoallをUpしてね！", description="</up:935190259111706754> でアップ。", color=discord.Color.green()), content=ment)
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_bump_distopia(self, message: discord.Message):
        if message.author.id == 1300797373374529557:
            try:
                if "表示順を上げました" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Distopia
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(embed=discord.Embed(title="Bumpを検知しました。", description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()))
                    await self.add_money(message)
                    await asyncio.sleep(7200)
                    await message.channel.send(embed=discord.Embed(title="DisTopiaをBumpしてね！", description="</bump:1309070135360749620> でBump。", color=discord.Color.green()), content=ment)
                elif "レートリミットです。" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Distopia
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Bumpに失敗しました。", description="しばらく待ってから、\n</bump:1309070135360749620> をお願いします。", color=discord.Color.red()))
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_vote_sabachannel(self, message: discord.Message):
        if message.author.id == 1233072112139501608:
            try:
                if "このサーバーに1票を投じました！" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].SabaChannel
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    next = message.embeds[0].fields[0].value.replace("<t:","").replace(":R>","")
                    ment = await self.mention_get(message)
                    await message.reply(embed=discord.Embed(title="Voteを検知しました。", description=f"<t:{next}:R>に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()))
                    await self.add_money(message)
                    await asyncio.sleep(int(next) - time.time())
                    await message.channel.send(embed=discord.Embed(title="鯖チャンネルをVoteしてね！", description="</vote:1233256792507682860> でVote。", color=discord.Color.green()), content=ment)
            except:
                return
            
    @commands.Cog.listener("on_message")
    async def on_message_bump_disboard(self, message: discord.Message):
        if message.author.id == 302050872383242240:
            try:
                if "表示順をアップ" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DisboardChannel
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(embed=discord.Embed(title="Bumpを検知しました。", description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()))
                    await self.add_money(message)
                    await asyncio.sleep(7200)
                    await message.channel.send(embed=discord.Embed(title="DisboardをBumpしてね！", description="</bump:947088344167366698> でBump。", color=discord.Color.green()), content=ment)
            except:
                return
            
    @commands.Cog.listener("on_message")
    async def on_message_up_discafe(self, message: discord.Message):
        if message.author.id == 850493201064132659:
            try:
                if "サーバーの表示順位を" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DiscafeChannel
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(embed=discord.Embed(title="Upを検知しました。", description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()))
                    await self.add_money(message)
                    await asyncio.sleep(3600)
                    await message.channel.send(embed=discord.Embed(title="DisCafeをUpしてね！", description="</up:980136954169536525> でUp。", color=discord.Color.green()), content=ment)
            except:
                return

    async def get_active_level(self, message: discord.Message):
        try:
            if not message.embeds:
                return "取得失敗"
            embed = message.embeds[0].fields[0].value.split("_**ActiveLevel ... ")[1].replace("**_", "")
            return f"{embed}"
        except:
            return "取得失敗"
        
    async def get_nokori_time(self, message: discord.Message):
        try:
            if not message.embeds:
                return "取得失敗"
            embed = message.embeds[0].fields[0].value.replace("間隔をあけてください(", "").replace(")", "")
            return embed
        except:
            return "取得失敗"

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_dissoku(self, before: discord.Message, after: discord.Message):
        if after.author.id == 761562078095867916:
            try:
                if "をアップしたよ!" in after.embeds[0].fields[0].name:
                    db = self.bot.async_db["Main"].DissokuChannel
                    try:
                        dbfind = await db.find_one({"Channel": after.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    acl = await self.get_active_level(after)
                    ment = await self.mention_get(after)
                    await after.reply(embed=discord.Embed(title="Upを検知しました。", description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}", color=discord.Color.green()).add_field(name="現在のアクティブレベル", value=f"{acl}レベル"))
                    await asyncio.sleep(7200)
                    await after.channel.send(embed=discord.Embed(title="ディス速をUpしてね！", description="</up:1363739182672904354> でアップ。", color=discord.Color.green()), content=ment)
                elif "失敗しました" in after.embeds[0].fields[0].name:
                    db = self.bot.async_db["Main"].DissokuChannel
                    try:
                        dbfind = await db.find_one({"Channel": after.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    nokori = await self.get_nokori_time(after)
                    await after.reply(embed=discord.Embed(title="Upに失敗しました。", description="しばらく待ってから</up:1363739182672904354>を実行してください。", color=discord.Color.red()).add_field(name="次Upできるまでの時間", value=f"{nokori}"))
            except:
                return    

    @commands.hybrid_group(name="bump", description="DicoallのUp通知を有効化します。", fallback="dicoall")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_dicoall(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Dicoall
        msg = await ctx.reply(embed=discord.Embed(title="Dicoallの通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Dicoallの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Dicoallの通知をOFFにしました。", color=discord.Color.red()))
        except:
            return
        
    @up_dicoall.command(name="distopia", description="DisTopiaの通知します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_distopia(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Distopia
        msg = await ctx.reply(embed=discord.Embed(title="Distopiaの通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Distopiaの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Distopiaの通知をOFFにしました。", color=discord.Color.red()))
        except:
            return
        
    @up_dicoall.command(name="sabachannel", description="鯖チャンネルの通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def sabachannel_vote(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].SabaChannel
        msg = await ctx.reply(embed=discord.Embed(title="鯖チャンネルの通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="鯖チャンネルの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="鯖チャンネルの通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return
        
    @up_dicoall.command(name="dissoku", description="ディス速の通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def dissoku_up(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].DissokuChannel
        msg = await ctx.reply(embed=discord.Embed(title="ディス速の通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="ディス速の通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="ディス速の通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return
        
    @up_dicoall.command(name="disboard", description="Disboardの通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def disboard_bump(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].DisboardChannel
        msg = await ctx.reply(embed=discord.Embed(title="Disboard通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Disboardの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Disboardの通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return
        
    @up_dicoall.command(name="discafe", description="DisCafeの通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def discafe_up(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].DiscafeChannel
        msg = await ctx.reply(embed=discord.Embed(title="DisCafe通知をONにしますか？", description="✅ .. ON\n❌ .. OFF", color=discord.Color.green()))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji == "✅":
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="DisCafeの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="DisCafeの通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return

    @up_dicoall.command(name="economy", description="Up・Bumpすると、UnbelievaBoatにお金を追加するようにします")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_economy(self, ctx: commands.Context, 金額: int):
        db = self.bot.async_db["Main"].BumpUpEconomy
        await db.replace_one(
            {"Channel": ctx.channel.id},
            {"Channel": ctx.channel.id, "Money": 金額},
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Up・Bumpに給料を追加しました。", color=discord.Color.green(), description=f"金額: {金額}").set_footer(text="現在Dissokuは未対応です。"))

    @up_dicoall.command(name="mention", description="Up・Bump通知時にロールをメンションします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_mention(self, ctx: commands.Context, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].BumpUpMention
        if not ロール:
            await db.delete_one(
                {"Channel": ctx.channel.id}
            )
            return await ctx.reply(embed=discord.Embed(title="Up・Bump通知時にロールを\n通知しないようにしました。", color=discord.Color.green()))
        await db.replace_one(
            {"Channel": ctx.channel.id},
            {"Channel": ctx.channel.id, "Role": ロール.id},
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Up・Bump通知時にロールを\n通知するようにしました。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(UpCog(bot))