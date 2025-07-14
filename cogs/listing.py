from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import io
import time
import asyncio
import re
import datetime
from functools import partial
import aiohttp
import time
import matplotlib.pyplot as plt
from discord import app_commands

class ListingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ListingCog")

    @commands.hybrid_group(name="listing", description="メンバーをリスト化します。", fallback="member")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def listing_member(self, ctx: commands.Context):
        await ctx.defer()
        member_list = ctx.guild.members
        spliting_member_list = [member_list[i: i+20] for i in range(0, len(member_list), 20)]
        def return_memberinfos(page: int):
            return "\n".join([f"{sm.name}({sm.id})" for sm in spliting_member_list[page-1]])
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(label="ページ番号",placeholder="数字を入力",style=discord.TextStyle.short,required=True)
                self.add_item(self.page)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"メンバーリスト ({len(member_list)}人)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")
        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await ctx.reply(embed=discord.Embed(title=f"メンバーリスト ({len(member_list)}人)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())


    @listing_member.command(name="role", description="ロールをリスト化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def listing_role(self, ctx: commands.Context):
        await ctx.defer()
        member_list = ctx.guild.roles
        if len(member_list) == 0:
            return await ctx.reply("ロールがありません。")
        spliting_member_list = [member_list[i: i+20] for i in range(0, len(member_list), 20)]
        def return_memberinfos(page: int):
            return "\n".join([f"{sm.name.replace("@", "")}({sm.id})" for sm in spliting_member_list[page-1]])
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(label="ページ番号",placeholder="数字を入力",style=discord.TextStyle.short,required=True)
                self.add_item(self.page)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"ロールリスト ({len(member_list)}個)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")
        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await ctx.reply(embed=discord.Embed(title=f"ロールリスト ({len(member_list)}個)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing_member.command(name="ban", description="Banしたメンバーをリスト化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def listing_ban(self, ctx: commands.Context):
        await ctx.defer()
        member_list = [b async for b in ctx.guild.bans()]
        if len(member_list) == 0:
            return await ctx.reply("Banされているメンバーはいません。")
        spliting_member_list = [member_list[i: i+20] for i in range(0, len(member_list), 20)]
        def return_memberinfos(page: int):
            return "\n".join([f"{sm.user.name}({sm.user.id})" for sm in spliting_member_list[page-1]])
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(label="ページ番号",placeholder="数字を入力",style=discord.TextStyle.short,required=True)
                self.add_item(self.page)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"BANリスト ({len(member_list)}人)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")
        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await ctx.reply(embed=discord.Embed(title=f"BANリスト ({len(member_list)}人)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing_member.command(name="guild-ban", description="認証時に検知する危険なサーバーリストを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def listing_guild_ban(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].GuildBAN
        member_list = [b async for b in db.find({"Guild": str(ctx.guild.id)})]
        if len(member_list) == 0:
            return await ctx.reply("Banされているサーバーはありません。")
        spliting_member_list = [member_list[i: i+20] for i in range(0, len(member_list), 20)]
        def return_memberinfos(page: int):
            return "\n".join([f"{sm["BANGuild"]}" for sm in spliting_member_list[page-1]])
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(label="ページ番号",placeholder="数字を入力",style=discord.TextStyle.short,required=True)
                self.add_item(self.page)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"BANサーバーリスト ({len(member_list)}サーバー)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")
        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await ctx.reply(embed=discord.Embed(title=f"BANサーバーリスト ({len(member_list)}サーバー)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing_member.command(name="analysis", description="統計を解析します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(内容=[
        app_commands.Choice(name='メンバーとBotの比率',value="mb"),
        app_commands.Choice(name='1ヶ月間の1日ごとのメンバー参加数',value="one_mem"),
        app_commands.Choice(name='グローバルなユーザーとBotの比率',value="gl_mb"),
    ])
    async def analysis_guild_or_user(self, ctx: commands.Context, 内容: app_commands.Choice[str]):
        await ctx.defer()
        if 内容.value == "mb":
            member_list = len(ctx.guild.members)
            bot_list = len([m for m in ctx.guild.members if m.bot])
            human_list = len([m for m in ctx.guild.members if not m.bot])
            json_data = {
                'labels': [
                    f'Members ({human_list})',
                    f'Bots ({bot_list})',
                ],
                'values': [
                    human_list / member_list,
                    bot_list / member_list
                ],
                'title': f'Member and Bot Ratio ({member_list})'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await ctx.reply(file=discord.File(io_, filename="piechart.png"))
                    io_.close()
        elif 内容.value == "one_mem":
            time_ = []
            count_ = []
            member_list = ctx.guild.members
            now = datetime.datetime.now(datetime.timezone.utc)

            for i in range(30):
                d = now - datetime.timedelta(days=i)
                label = i
                time_.append(label)

                matched_members = [
                    member for member in member_list
                    if member.joined_at and abs((member.joined_at - d).days) == 0
                ]
                count_.append(len(matched_members))

            json_data = {
                'xvalues': time_[::-1],
                'yvalues': count_[::-1],
                'title': "Number of members participating"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/plot", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await ctx.reply(file=discord.File(io_, filename="join_chart.png"))
                    io_.close()
        elif 内容.value == "gl_mb":
            member_list = len(self.bot.users)
            bot_list = len([m for m in self.bot.users if m.bot])
            human_list = len([m for m in self.bot.users if not m.bot])
            json_data = {
                'labels': [
                    f'Users ({human_list})',
                    f'Bots ({bot_list})',
                ],
                'values': [
                    human_list / member_list,
                    bot_list / member_list
                ],
                'title': f'User and Bot Ratio ({member_list})'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await ctx.reply(file=discord.File(io_, filename="piechart.png"))
                    io_.close()

    @listing_member.command(name="graph", description="グラフを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(内容=[
        app_commands.Choice(name='円グラフ',value="pie"),
        app_commands.Choice(name='折れ線グラフ', value="line"),
    ])
    async def graph_make(self, ctx: commands.Context, 内容: app_commands.Choice[str], タイトル: str = "Graph"):
        if 内容.value == "pie":
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="円グラフの設定", timeout=None)
                    self.datas = discord.ui.TextInput(label="データ (「ラベル|データ」 と入力)",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.datas)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(ephemeral=True)
                    try:
                        data = self.datas.value.split("\n")
                        labels = []
                        values = []
                        for d in data:
                            label, value = d.split("|")
                            labels.append(label)
                            values.append(int(value))
                        if len(labels) != len(values):
                            raise ValueError("ラベルとデータの数が一致しません。")
                    except Exception as e:
                        return await interaction.followup.send(ephemeral=True, content="エラーが発生しました。")
                    json_data = {
                        'labels': labels,
                        'values': values,
                        'title': タイトル
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                            io_ = io.BytesIO(await response.read())
                            await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                            io_.close()
            await ctx.interaction.response.send_modal(send())
        elif 内容.value == "line":
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="折れ線グラフの設定", timeout=None)
                    self.xdatas = discord.ui.TextInput(label="Xのデータ (,で区切る)",placeholder="1,2,3",style=discord.TextStyle.long,required=True)
                    self.add_item(self.xdatas)
                    self.ydatas = discord.ui.TextInput(label="Yのデータ (,で区切る)",placeholder="1,2,3",style=discord.TextStyle.long,required=True)
                    self.add_item(self.ydatas)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(ephemeral=True)
                    try:
                        x = []
                        y = []
                        xdata = self.xdatas.value.split(",")
                        for d in xdata:
                            if not d.isdigit():
                                return await interaction.followup.send(ephemeral=True, content="Xのデータは数字でなければなりません。")
                            x.append(int(d))
                        ydata = self.ydatas.value.split(",")
                        for d in ydata:
                            if not d.isdigit():
                                return await interaction.followup.send(ephemeral=True, content="Yのデータは数字でなければなりません。")
                            y.append(int(d))
                        if len(x) != len(y):
                            return await interaction.followup.send(ephemeral=True, content="XとYのデータの数が一致しません。")
                    except Exception as e:
                        return await interaction.followup.send(ephemeral=True, content="エラーが発生しました。")
                    json_data = {
                        'xvalues': x,
                        'yvalues': y,
                        'title': タイトル
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("http://localhost:3067/plot", json=json_data) as response:
                            io_ = io.BytesIO(await response.read())
                            await interaction.followup.send(file=discord.File(io_, filename="plot.png"))
                            io_.close()
            await ctx.interaction.response.send_modal(send())

async def setup(bot):
    await bot.add_cog(ListingCog(bot))