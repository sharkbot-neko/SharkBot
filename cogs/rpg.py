from discord.ext import commands
import discord
import random
from discord import app_commands

class RPGCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.ITEM_CHOICES = {
                "red_color": "ユーザーの色を赤に変更 (1ポイント)",
                "yellow_color": "ユーザーの色を黄に変更 (1ポイント)",
                "blue_color": "ユーザーの色を青に変更 (1ポイント)",
                "random_color": "ユーザーの色をランダムに変更 (5ポイント)",
                "viproom": "VIPルームにアクセス (10ポイント)",
                "beta": "sharkbotの実装予定機能にアクセス (10ポイント)",
                "gold": "錬金術研究所 (100ポイント)",
                "pfact": "ポイント工場 (300ポイント)",
                "callm": "召喚獣 (10ポイント)",
                "takarakuji": "宝くじ (50ポイント)",
                "nekoserver": "身内鯖招待 (100ポイント)"
            }
        
        self.takarakuji = [10, 30, 50, 100, 500, 300, 0, 0, 0, 0]

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
        
    async def add_sharkpoint(self, ctx: commands.Context, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": ctx.author.id})
        if user_data:
            await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": coin}})
            return True
        else:
            return False

    async def set_user_color(self, ctx: commands.Context, color: str):
        db = self.bot.async_db["Main"].UserColor
        await db.replace_one(
            {"User": ctx.author.id}, 
            {"User": ctx.author.id, "Color": color}, 
            upsert=True
        )

    async def add_shokan_juu_user(self, ctx: commands.Context, user: discord.User):
        db = self.bot.async_db["Main"].CallBeasts
        await db.update_one(
            {"User": ctx.author.id},
            {"$addToSet": {"pet": user.id}},
            upsert=True
        )

    @commands.hybrid_command(name="point", description="Sharkポイントの管理をするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(行動=[
        app_commands.Choice(name='残高照会',value="bal"),
    ])
    async def sharkpoint_check(self, ctx: commands.Context, 行動: app_commands.Choice[str]):
        await ctx.defer()
        val = 行動.value
        if val == "bal":
            db = self.bot.async_db["Main"].SharkBotInstallPoint
            try:
                dbfind = await db.find_one({"_id": ctx.author.id}, {"_id": False})
            except:
                return await ctx.reply(embed=discord.Embed(title="Sharkポイント 残高照会", description="0ポイント", color=discord.Color.blue()))
            if dbfind is None:
                return await ctx.reply(embed=discord.Embed(title="Sharkポイント 残高照会", description="0ポイント"))
            return await ctx.reply(embed=discord.Embed(title="Sharkポイント 残高照会", description=f"{dbfind["count"]}ポイント", color=discord.Color.blue()))

    async def item_autocomplete(
        self, 
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=name, value=value)
            for value, name in self.ITEM_CHOICES.items()
            if current.lower() in name.lower()
        ][:25]

    @commands.hybrid_command(name="shop", description="sharkポイントを使っていろいろな商品を買えるよ。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.autocomplete(商品=item_autocomplete)
    async def sharkpoint_shop(self, ctx: commands.Context, 商品: str):
        await ctx.defer()
        val = self.ITEM_CHOICES.get(商品, "不明な商品")
        if val == "ユーザーの色を赤に変更 (1ポイント)":
            check = await self.remove_sharkpoint(ctx, 1)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には1ポイントが必要です。", color=discord.Color.red()))
            await self.set_user_color(ctx, "red")
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="ユーザーの色を赤にしました。", color=discord.Color.green()))
        elif val == "ユーザーの色を黄に変更 (1ポイント)":
            check = await self.remove_sharkpoint(ctx, 1)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には1ポイントが必要です。", color=discord.Color.red()))
            await self.set_user_color(ctx, "yellow")
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="ユーザーの色を黄にしました。", color=discord.Color.green()))
        elif val == "ユーザーの色を青に変更 (1ポイント)":
            check = await self.remove_sharkpoint(ctx, 1)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には1ポイントが必要です。", color=discord.Color.red()))
            await self.set_user_color(ctx, "blue")
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="ユーザーの色を青にしました。", color=discord.Color.green()))
        elif val == "ユーザーの色をランダムに変更 (5ポイント)":
            check = await self.remove_sharkpoint(ctx, 5)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には5ポイントが必要です。", color=discord.Color.red()))
            await self.set_user_color(ctx, "random")
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="ユーザーの色をランダムにしました。", color=discord.Color.green()))
        elif val == "VIPルームにアクセス (10ポイント)":
            if not self.bot.get_guild(1343124570131009579).get_member(ctx.author.id):
                return await ctx.reply(embed=discord.Embed(title="条件を満たしていません。", description="SharkBot公式サーバーに入ってください。", color=discord.Color.red()))
            if self.bot.get_guild(1343124570131009579).get_role(1359843498395959437) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
                return await ctx.reply(embed=discord.Embed(title="すでに購入しています！", description="すでに購入しています。", color=discord.Color.red()))
            check = await self.remove_sharkpoint(ctx, 10)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には10ポイントが必要です。", color=discord.Color.red()))
            role = self.bot.get_guild(1343124570131009579).get_role(1359843498395959437)
            await self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).add_roles(role)
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="SharkBot公式サーバーの\nVIPルームに入れるようになりました。", color=discord.Color.green()))
        elif val == "sharkbotの実装予定機能にアクセス (10ポイント)":
            if not self.bot.get_guild(1343124570131009579).get_member(ctx.author.id):
                return await ctx.reply(embed=discord.Embed(title="条件を満たしていません。", description="SharkBot公式サーバーに入ってください。", color=discord.Color.red()))
            if self.bot.get_guild(1343124570131009579).get_role(1359881876856111325) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
                return await ctx.reply(embed=discord.Embed(title="すでに購入しています！", description="すでに購入しています。", color=discord.Color.red()))
            check = await self.remove_sharkpoint(ctx, 10)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には10ポイントが必要です。", color=discord.Color.red()))
            role = self.bot.get_guild(1343124570131009579).get_role(1359881876856111325)
            await self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).add_roles(role)
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="SharkBot公式サーバーの\nベータ版ルームに入れるようになりました。", color=discord.Color.green()))
        elif val == "錬金術研究所 (100ポイント)":
            check = await self.remove_sharkpoint(ctx, 100)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には100ポイントが必要です。", color=discord.Color.red()))
            async def add_gold(ctx: commands.Context):
                db = self.bot.async_db["Main"].SharkBotGoldPoint
                user_data = await db.find_one({"_id": ctx.author.id})
                if user_data:
                    await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": 1}})
                    return True
                else:
                    await db.insert_one({"_id": ctx.author.id, "count": 1})
                    return True
            await add_gold(ctx)
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="錬金術研究所を購入しました。", color=discord.Color.green()))
        elif val == "ポイント工場 (300ポイント)":
            check = await self.remove_sharkpoint(ctx, 300)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には300ポイントが必要です。", color=discord.Color.red()))
            async def add_pfact(ctx: commands.Context):
                db = self.bot.async_db["Main"].SharkBotPointFactory
                user_data = await db.find_one({"_id": ctx.author.id})
                if user_data:
                    await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": 1}})
                    return True
                else:
                    await db.insert_one({"_id": ctx.author.id, "count": 1})
                    return True
            await add_pfact(ctx)
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description="ポイント工場を購入しました。", color=discord.Color.green()))
        elif val == "召喚獣 (10ポイント)":
            check = await self.remove_sharkpoint(ctx, 10)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には10ポイントが必要です。", color=discord.Color.red()))
            us = random.choice([u for u in ctx.guild.members])
            await self.add_shokan_juu_user(ctx, us)
            await ctx.reply(embed=discord.Embed(title="商品を購入しました。", description=f"召喚獣 ({us.display_name})を購入しました。", color=discord.Color.green()))
        elif val == "宝くじ (50ポイント)":
            check = await self.remove_sharkpoint(ctx, 50)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には50ポイントが必要です。", color=discord.Color.red()))
            kekka = random.choice(self.takarakuji)
            await self.add_sharkpoint(ctx, kekka)
            await ctx.reply(embed=discord.Embed(title="宝くじを引きました。", description=f"{kekka}ポイントが当たりました。", color=discord.Color.pink()))
        elif val == "身内鯖招待 (100ポイント)":
            check = await self.remove_sharkpoint(ctx, 100)
            if not check:
                return await ctx.reply(embed=discord.Embed(title="ポイントが足りません。", description="商品の購入には100ポイントが必要です。", color=discord.Color.red()))
            await ctx.author.send("身内鯖の招待リンク\n外部に流出させないでください。\nhttps://discord.gg/wP6wWNMjeh")
            await self.bot.get_channel(1381126369416708248).send(content=f"{ctx.author.mention}さんを身内鯖に招待しました。")
            return await ctx.reply(embed=discord.Embed(title="身内鯖に招待しました。", description=f"よろしくね！", color=discord.Color.pink()))
        else:
            return await ctx.reply(embed=discord.Embed(title="その商品はありません。", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(RPGCog(bot))