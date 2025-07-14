from discord.ext import commands
import datetime
import discord
from discord import app_commands
from functools import partial
import time

class NickNameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> NickNameCog")

    @commands.hybrid_group(name="nick", description="ニックネームを編集します。", fallback="edit")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_nicknames=True)
    async def nick_edit(self, ctx: commands.Context, メンバー: discord.Member, 名前: str):
        try:
            await ctx.defer()
            await メンバー.edit(nick=名前)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ニックネームを編集しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ニックネームを編集できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @nick_edit.command(name="reset", description="ニックネームをリセットします。")
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nick_reset(self, ctx: commands.Context, メンバー: discord.Member):
        try:
            await ctx.defer()
            await メンバー.edit(nick=None)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ニックネームをリセットしました。", color=discord.Color.green(), description=f"{メンバー.mention}のニックネームをリセットしました。"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ニックネームをリセットできませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @nick_edit.command(name="split", description="ニックネームを切り分けて、片方を残します。")
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(どっちを残すか=[
        app_commands.Choice(name='前',value="mae"),
        app_commands.Choice(name='後ろ',value="usi"),
    ])
    async def nick_split(self, ctx: commands.Context, メンバー: discord.Member, 切り分けるテキスト: str, どっちを残すか: app_commands.Choice[str]):
        try:
            await ctx.defer()
            nickname = メンバー.display_name
            if どっちを残すか.value == "mae":
                sp = nickname.split(切り分けるテキスト)[0]
            else:
                sp = nickname.split(切り分けるテキスト)[1]
            await メンバー.edit(nick=sp)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ニックネームを切り分けました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ニックネームを切り分けできませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @nick_edit.command(name="profile-delete", description="プロフに自鯖などをニックネームから削除します。")
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nick_profile_delete(self, ctx: commands.Context, メンバー: discord.Member):
        try:
            nickname = メンバー.display_name
            profile_list = ["プロフに", "プロフィールに", "プロフィに", "Profileに"]
            for p in profile_list:
                nickname = nickname.split(p)[0].replace(p, "")
            await メンバー.edit(nick=nickname)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> プロフに自鯖などを削除しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> プロフに自鯖などを削除できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

async def setup(bot):
    await bot.add_cog(NickNameCog(bot))