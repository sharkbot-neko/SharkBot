from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import aiohttp
import re
from functools import partial
import time

class LoginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LoginCog")

    async def get_account(self, username: str, password: str):
        db = self.bot.async_db["Main"].SharkAccountData
        try:
            dbfind = await db.find_one({"UserName": username, "Password": password}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind.get("UserName", None)

    @commands.hybrid_group(name="account", description="アカウントを登録します。", fallback="register")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def account_register(self, ctx: commands.Context):
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="アカウントの登録", timeout=None)
                self.username = discord.ui.TextInput(label="ユーザー名",placeholder="ユーザー名を入力",style=discord.TextStyle.short,required=True)
                self.password = discord.ui.TextInput(label="パスワード (他人に渡さないでください)",placeholder="パスワードを入力",style=discord.TextStyle.short,required=True)
                self.add_item(self.username)
                self.add_item(self.password)
            async def get_account(self, interaction, username: str):
                db = interaction.client.async_db["Main"].SharkAccountData
                try:
                    dbfind = await db.find_one({"UserName": username}, {"_id": False})
                except:
                    return None
                if dbfind is None:
                    return None
                return dbfind.get("UserName", None)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await interaction.response.defer(ephemeral=True)
                if self.username.value == "Guest":
                    return await interaction.followup.send(ephemeral=True, content="すでにアカウントが存在します。\nユーザー名を変えて登録してください。")
                if self.password.value == "0000":
                    return await interaction.followup.send(ephemeral=True, content="すでにアカウントが存在します。\nユーザー名を変えて登録してください。")
                check = await self.get_account(interaction, self.username.value)
                if check:
                    return await interaction.followup.send(ephemeral=True, content="すでにアカウントが存在します。\nユーザー名を変えて登録してください。")
                db = interaction.client.async_db["Main"].SharkAccountData
                await db.replace_one(
                    {"UserName": self.username.value, "UserID": interaction.user.id}, 
                    {"UserName": self.username.value, "Password": self.password.value, "UserID": interaction.user.id}, 
                    upsert=True
                )
                await interaction.followup.send(ephemeral=True, content="アカウントを登録しました。")
        await ctx.interaction.response.send_modal(send())

    @account_register.command(name="info", description="アカウント情報を取得します。")
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def account_info(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        db = self.bot.async_db["Main"].SharkAccountData
        try:
            dbfind = await db.find_one({"UserID": ctx.author.id}, {"_id": False})
        except:
            return await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントの情報", description=f"まだログインしていません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントの情報", description=f"まだログインしていません。", color=discord.Color.red()))
        await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントの情報", description=f"ユーザー名: {dbfind.get("UserName")}\nパスワード: {dbfind.get("Password")}", color=discord.Color.green()))

    @account_register.command(name="dashboard", description="アカウントのダッシュボードにアクセスします。")
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def account_dashboard(self, ctx: commands.Context):
        if not ctx.interaction:
            return await ctx.reply(content="スラッシュコマンドから実行してください。")
        await ctx.defer(ephemeral=True)
        db = self.bot.async_db["Main"].SharkAccountData
        try:
            dbfind = await db.find_one({"UserID": ctx.author.id}, {"_id": False})
        except:
            return await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントのダッシュボード", description=f"まだログインしていません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントのダッシュボード", description=f"まだログインしていません。", color=discord.Color.red()))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="アクセスする", url=f"https://api.sharkbot.xyz/account?username={dbfind.get("UserName")}&password={dbfind.get("Password")}"))
        await ctx.reply(ephemeral=True, embed=discord.Embed(title="アカウントのダッシュボード", description="外部にurlを漏らさないでください。", color=discord.Color.green()), view=view)

async def setup(bot):
    await bot.add_cog(LoginCog(bot))