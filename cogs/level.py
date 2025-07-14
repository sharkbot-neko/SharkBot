from discord.ext import commands
import discord
import traceback
import sys
import logging
import asyncio
from PIL import Image, ImageDraw, ImageFont
import asyncio
import aiohttp
import io
import random

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LevelCog")

    async def check_level_enabled(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        else:
            return True

    async def new_user_write(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id}, 
                {"Guild": guild.id, "User": user.id, "Level": 0, "XP": 1}, 
                upsert=True
            )
        except:
            return
        
    async def user_write(self, guild: discord.Guild, user: discord.User, level: int, xp: int):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id}, 
                {"Guild": guild.id, "User": user.id, "Level": level, "XP": xp}, 
                upsert=True
            )
        except:
            return
        
    async def get_level(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Level"]
        except:
            return
        
    async def get_xp(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["XP"]
        except:
            return
        
    async def set_user_image(self, user: discord.User, url: str):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            await db.replace_one(
                {"User": user.id}, 
                {"User": user.id, "Image": url}, 
                upsert=True
            )
        except:
            return
        
    async def get_user_image(self, user: discord.User):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            try:
                dbfind = await db.find_one({"User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Image"]
        except:
            return
        
    async def set_channel(self, guild: discord.Guild, channel: discord.TextChannel = None):
        try:
            if channel == None:
                db = self.bot.async_db["Main"].LevelingUpAlertChannel
                await db.delete_one(
                    {"Guild": guild.id}
                )
                return
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id}, 
                {"Guild": guild.id, "Channel": channel.id}, 
                upsert=True
            )
        except:
            return

    async def get_channel(self, guild: discord.Guild):
        try:
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            try:
                dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Channel"]
        except:
            return
        
    async def set_role(self, guild: discord.Guild, level: int, role: discord.Role = None, ):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            if role is None:
                await db.delete_one({"Guild": guild.id})
                return
            
            await db.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id, "Role": role.id, "Level": level}, 
                upsert=True
            )
        except Exception as e:
            print(f"Error in set_role: {e}")

    async def get_role(self, guild: discord.Guild, level: int):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            dbfind = await db.find_one({"Guild": guild.id, "Level": level}, {"_id": False})
            return dbfind["Role"] if dbfind else None
        except Exception as e:
            return None
        
    async def get_timing(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingUpTiming
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            return dbfind["Timing"] if dbfind else None
        except Exception as e:
            return None

    @commands.Cog.listener("on_message")
    async def on_message_level(self, message: discord.Message):
        if message.author.bot:
            return
        try:
            enabled = await self.check_level_enabled(message.guild)
        except:
            return
        if enabled:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": message.guild.id, "User": message.author.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return await self.new_user_write(message.guild, message.author)
            else:
                await self.user_write(message.guild, message.author, dbfind["Level"], dbfind["XP"] + random.randint(0, 2))
                xp = await self.get_xp(message.guild, message.author)
                timing = await self.get_timing(message.guild)
                tm = 100
                if not timing is None:
                    tm = timing
                if xp > tm:
                    lv = await self.get_level(message.guild, message.author)
                    await self.user_write(message.guild, message.author, lv + 1, 0)
                    lvg = await self.get_level(message.guild, message.author)
                    cha = await self.get_channel(message.guild)
                    role = await self.get_role(message.guild, lvg)
                    if role:
                        grole = message.guild.get_role(role)
                        if grole:
                            await message.author.add_roles(grole)
                    try:
                        if cha:
                            await self.bot.get_channel(cha).send(embed=discord.Embed(title=f"`{message.author.name}`さんの\nレベルが{lvg}になったよ！", color=discord.Color.gold()))
                        else:
                            return await message.reply(f"レベルが「{lvg}レベル」になったよ！")
                    except:
                        return
        else:
            return

    @commands.hybrid_group(name="level", description="レベルを有効化&無効化します。", fallback="setting")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_setting(self, ctx):
        await ctx.defer()
        db = self.bot.async_db["Main"].LevelingSetting
        msg = await ctx.reply(embed=discord.Embed(title="レベリングをONにしますか？", description=f"<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Guild": ctx.guild.id},
                    {"Guild": ctx.guild.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="レベリングをONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Guild": ctx.guild.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="レベリングをOFFにしました。", color=discord.Color.red()))
        except:
            return await ctx.reply(f"{sys.exc_info()}")
        
    @level_setting.command(name="show", description="レベルを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_show(self, ctx: commands.Context):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return
        if ctx.author.avatar:
            avatar = ctx.author.avatar.url
        else:
            avatar = ctx.author.default_avatar.url
        if enabled:
            lv = await self.get_level(ctx.guild, ctx.author)
            if lv == None:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「0レベル」\nXP: 「0XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
            xp = await self.get_xp(ctx.guild, ctx.author)
            if xp == None:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「0レベル」\nXP: 「0XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
            await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「{lv}レベル」\nXP: 「{xp}XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        
    @level_setting.command(name="channel", description="レベルアップの通知のチャンネルを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_channel(self, ctx, チャンネル: discord.TextChannel = None):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return
        if enabled:
            if チャンネル:
                await self.set_channel(ctx.guild, チャンネル)
                await ctx.reply(embed=discord.Embed(title="レベルアップの通知チャンネルを設定しました。", color=discord.Color.green()))
            else:
                await self.set_channel(ctx.guild)
                await ctx.reply(embed=discord.Embed(title="レベルアップの通知チャンネルを削除しました。", color=discord.Color.green()))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))

    @level_setting.command(name="role", description="特定のレベルになるとロールを付けます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def level_role(self, ctx, レベル: int, ロール: discord.Role = None):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if enabled:
            if not ロール:
                await self.set_role(ctx.guild, レベル)
                return await ctx.reply(embed=discord.Embed(title=f"{レベル}レベルになってもロールをもらえなくしました。", color=discord.Color.green()))
            await self.set_role(ctx.guild, レベル, ロール)
            return await ctx.reply(embed=discord.Embed(title=f"{レベル}レベルになるとロールを付与するようにしました。", color=discord.Color.green()))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))

    @level_setting.command(name="edit", description="レベルを編集します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_edit(self, ctx: commands.Context, ユーザー: discord.User, レベル: int, xp: int):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if not enabled:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        await self.user_write(ctx.guild, ユーザー, レベル, xp)
        return await ctx.reply(embed=discord.Embed(title="レベルを編集しました。", description=f"ユーザー: 「{ユーザー.name}」\nレベル: 「{レベル}レベル」\nXP: 「{xp}XP」", color=discord.Color.green()))
    
    @level_setting.command(name="timing", description="レベルアップするタイミングを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_timing(self, ctx: commands.Context, xp: int):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if not enabled:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if xp < 21:
            return await ctx.reply(embed=discord.Embed(title="レベルアップするタイミングは20以上でお願いします。", color=discord.Color.green()))
        db = self.bot.async_db["Main"].LevelingUpTiming
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Timing": xp}, 
            upsert=True
        )
        return await ctx.reply(embed=discord.Embed(title="レベルアップするタイミングを設定しました。", color=discord.Color.green(), description=f"タイミング: {xp}XP"))
    
    @level_setting.command(name="rewards", description="レベルアップ時のご褒美をリスト化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_rewards(self, ctx: commands.Context):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if not enabled:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].LevelingUpRole
        roles_cursor = db.find({"Guild": ctx.guild.id})
        roles_list = await roles_cursor.to_list(length=None)
        
        description_lines = []
        for r in roles_list:
            role_id = r.get("Role", 0)
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else "不明なロール"
            description_lines.append(f"{r.get("Level", "?")}. {role_name}")

        await ctx.reply(embed=discord.Embed(title="レベルアップ時のご褒美リスト", color=discord.Color.yellow()).add_field(name="ご褒美ロール", value=f"\n".join(description_lines)))

    @level_setting.command(name="ranking", description="レベルのランキングを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_ranking(self, ctx: commands.Context):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if not enabled:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        db = self.bot.async_db["Main"].Leveling
        top_users = await db.find({"Guild": ctx.guild.id}).sort("Level", -1).limit(5).to_list(length=5)
        msg = ""
        for index, user_data in enumerate(top_users, start=1):
            member = self.bot.get_user(user_data["User"])
            username = f"{member.display_name}" if member else f"Unknown ({user_data["User"]})"
            msg += f"{index}.**{username}** - {user_data["Level"]}レベル\n"
        return await ctx.reply(embed=discord.Embed(title="このサーバーでのランキング", description=msg, color=discord.Color.yellow()))

async def setup(bot):
    await bot.add_cog(LevelCog(bot))