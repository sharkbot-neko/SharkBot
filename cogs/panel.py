from discord.ext import commands
import discord
import traceback
import re
import sys
import logging
import aiohttp
import time
import ssl
import libcontainer as container
import random
from functools import partial
import json
import asyncio
import datetime
import string
import io
import requests

tku_cooldown = {}
freech = []

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class UserSetting():
    def __init__(self, username: str, color: str = "#000000"):
        self._username = username
        self._color = color

    @property
    def name(self):
        return self._username
    
    @property
    def color(self):
        return self._color
    
class Chaat:
    def __init__(self, hashid: str = None):
        self.ses = requests.Session()
        self.token_pat = r"[a-zA-Z0-9]{32}"
        self.token = None
        self.hash_id = hashid

    def login(self):
        res = self.ses.get("https://c.kuku.lu/")
        token = re.search(self.token_pat, res.text).group()
        self.token = token
        return True
    
    def create_room(self):
        data = {
            'action': 'createRoom',
            'csrf_token_check': self.token,
        }

        response = self.ses.post('https://c.kuku.lu/api_server.php', data=data)

        return response.json()
    
    def send_room(self, text: str, hash: str = None):
        if hash:
            data = {
                'action': 'sendData',
                'hash': hash,
                'profile_name': '匿名とむ',
                'profile_color': '#000000',
                'data': '{"type":"chat","msg":"' + text +'"}',
                'csrf_token_check': self.token,
            }

            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()
        else:
            if not self.hash_id:
                return {"Error": "ハッシュIDが設定されていません。"}
            data = {
                'action': 'sendData',
                'hash': self.hash_id,
                'profile_name': '匿名とむ',
                'profile_color': '#000000',
                'data': '{"type":"chat","msg":"' + text +'"}',
                'csrf_token_check': self.token,
            }

            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()
        
    def edit_user(self, usersetting: UserSetting, hash: str = None):
        if hash:
            data = {
                'action': 'changeMyProfile',
                'hash': hash,
                'new_name': usersetting.name,
                'new_trip': '',
                'new_color': usersetting.color,
                'csrf_token_check': self.token,
            }

            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()
        else:
            if not self.hash_id:
                return {"Error": "ハッシュIDが設定されていません。"}
            data = {
                'action': 'changeMyProfile',
                'hash': self.hash_id,
                'new_name': usersetting.name,
                'new_trip': '',
                'new_color': usersetting.color,
                'csrf_token_check': self.token,
            }
            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()
    
    def generate_current_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d%H%M%S")

    def fetch_room(self, hash: str = None):
        if hash:
            data = {
                'action': 'fetchData',
                'hash': hash,
                'csrf_token_check': self.token,
                'mode': 'log',
                'type': 'last',
                'num': self.generate_current_timestamp(),
            }

            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()
        else:
            if not self.hash_id:
                return {"Error": "ハッシュIDが設定されていません。"}
            data = {
                'action': 'fetchData',
                'hash': self.hash_id,
                'csrf_token_check': self.token,
                'mode': 'log',
                'type': 'last',
                'num': self.generate_current_timestamp(),
            }

            response = self.ses.post('https://c.kuku.lu/room.php', data=data)

            return response.json()

class AuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role):
        super().__init__()

        a = random.randint(-999, 999)
        self.kekka = str(abs(a))
        self.r = role

        self.name = discord.ui.TextInput(label=f"{a}の絶対値は？")
        self.add_item(self.name)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send(f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True)
        else:
            await interaction.response.send_message("認証に失敗しました。", ephemeral=True)

class PlusAuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role, drole: discord.Role):
        super().__init__()

        a = random.randint(-999, 999)
        self.kekka = str(abs(a))
        self.r = role
        self.dr = drole

        self.name = discord.ui.TextInput(label=f"{a}の絶対値は？")
        self.add_item(self.name)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.remove_roles(self.dr)
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send(f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True)
        else:
            await interaction.response.send_message("認証に失敗しました。", ephemeral=True)

class ObjModal(discord.ui.Modal, title="異議申し立てをする"):
    def __init__(self):
        super().__init__()

        self.text_ = discord.ui.TextInput(label=f"異議申し立てする内容を入力", style=discord.TextStyle.long, required=True)
        self.add_item(self.text_)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            db = interaction.client.async_db["Main"].ObjReq
            try:
                dbfind = await db.find_one({"Guild": interaction.guild.id, "User": interaction.user.id}, {"_id": False})
            except:
                return await interaction.followup.send("エラーが発生しました。", ephemeral=True)
            if not dbfind is None:
                return await interaction.followup.send("異議申し立てが完了していません。\n完了してから再度お越しください。", ephemeral=True)
            await db.replace_one(
                {"Guild": interaction.guild.id, "User": interaction.user.id}, 
                {"Guild": interaction.guild.id, "User": interaction.user.id}, 
                upsert=True
            )
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="受諾", custom_id=f"obj_ok+{interaction.guild.id}+{interaction.user.id}", style=discord.ButtonStyle.blurple))
            view.add_item(discord.ui.Button(label="拒否", custom_id=f"obj_no+{interaction.guild.id}+{interaction.user.id}", style=discord.ButtonStyle.blurple))
            await interaction.guild.owner.send(embed=discord.Embed(title=f"「{interaction.guild.name}」に対して\n異議申し立てされました。", description=f"```{self.text_.value}```", color=discord.Color.red()).add_field(name="ユーザー名", value=f"{interaction.user.name}/{interaction.user.id}", inline=False), view=view)
            await interaction.followup.send("異議申し立てが完了しました。", ephemeral=True)
        except:
            await interaction.followup.send(f"エラーが発生しました。\n{sys.exc_info()}", ephemeral=True)

class PanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> PanelCog")

    async def send_beta_view(self, channel: int, components: list):
        url = f"https://discord.com/api/v10/channels/{channel}/messages"
        headers = {
            "Authorization": f"Bot {self.bot.http.token}",
            "Content-Type": "application/json"
        }
        data = {
            "flags": 32768,
            "components": components
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.json()

    @commands.hybrid_group(name="panel", description="ロールパネルを作ります。", fallback="role")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def role_panel(self, ctx: commands.Context, タイトル: str, 説明: str, メンションを表示するか: bool, ロール1: discord.Role, ロール2: discord.Role = None, ロール3: discord.Role = None, ロール4: discord.Role = None, ロール5: discord.Role = None, ロール6: discord.Role = None, ロール7: discord.Role = None, ロール8: discord.Role = None, ロール9: discord.Role = None, ロール10: discord.Role = None):
        view = discord.ui.View()
        ls = []
        view.add_item(discord.ui.Button(label=f"{ロール1.name}", custom_id=f"rolepanel_v1+{ロール1.id}"))
        ls.append(f"{ロール1.mention}")
        try:
            view.add_item(discord.ui.Button(label=f"{ロール2.name}", custom_id=f"rolepanel_v1+{ロール2.id}"))
            ls.append(f"{ロール2.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール3.name}", custom_id=f"rolepanel_v1+{ロール3.id}"))
            ls.append(f"{ロール3.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール4.name}", custom_id=f"rolepanel_v1+{ロール4.id}"))
            ls.append(f"{ロール4.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール5.name}", custom_id=f"rolepanel_v1+{ロール5.id}"))
            ls.append(f"{ロール5.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール6.name}", custom_id=f"rolepanel_v1+{ロール6.id}"))
            ls.append(f"{ロール6.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール7.name}", custom_id=f"rolepanel_v1+{ロール7.id}"))
            ls.append(f"{ロール7.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール8.name}", custom_id=f"rolepanel_v1+{ロール8.id}"))
            ls.append(f"{ロール8.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール9.name}", custom_id=f"rolepanel_v1+{ロール9.id}"))
            ls.append(f"{ロール9.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール10.name}", custom_id=f"rolepanel_v1+{ロール10.id}"))
            ls.append(f"{ロール10.mention}")
        except:
            pass
        embed = discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green())
        if メンションを表示するか:
            embed.add_field(name="ロール一覧", value=f"\n".join(ls))
        await ctx.channel.send(embed=embed, view=view)
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    async def message_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            messages = []
            async for m in interaction.channel.history(limit=50):
                messages.append(m)
            choices = []

            for message in messages:
                if not message.embeds:
                    continue
                if current.lower() in message.embeds[0].title.lower():
                    choices.append(discord.app_commands.Choice(name=message.embeds[0].title[:100], value=str(message.id)))

                if len(choices) >= 25:
                    break

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @role_panel.command(description="ロールパネルを編集します。", name="role-edit")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    @discord.app_commands.autocomplete(ロールパネルのid=message_autocomplete)
    @discord.app_commands.choices(
        削除か追加か=[
            discord.app_commands.Choice(name="追加", value="add"),
            discord.app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def panel_rolepanel_edit(self, ctx: commands.Context, ロールパネルのid: str, ロール: discord.Role, 削除か追加か: discord.app_commands.Choice[str]):
        await ctx.defer(ephemeral=True)
        try:
            ロールパネルのid_ = await ctx.channel.fetch_message(int(ロールパネルのid))
        except:
            return await ctx.reply(embed=discord.Embed(title="メッセージが見つかりません", color=discord.Color.red()), ephemeral=True)
        view = discord.ui.View()
        for action_row in ロールパネルのid_.components:
            for v in action_row.children:
                if isinstance(v, discord.Button):
                    view.add_item(discord.ui.Button(label=v.label, custom_id=v.custom_id))

        if 削除か追加か.name == "追加":
            view.add_item(discord.ui.Button(label=ロール.name, custom_id=f"rolepanel_v1+{ロール.id}"))

        else:
            view = discord.ui.View()
            for action_row in ロールパネルのid_.components:
                for v in action_row.children:
                    if isinstance(v, discord.Button):
                        if not v.label == ロール.name:
                            view.add_item(discord.ui.Button(label=v.label, custom_id=v.custom_id))
        embed = ロールパネルのid_.embeds[0]

        if embed.fields:
            field_value = embed.fields[0].value or ""
            
            if 削除か追加か.name == "追加":
                field_value += f"\n{ロール.mention}"
            elif 削除か追加か.name == "削除":
                field_value = field_value.replace(f"\n{ロール.mention}", "").replace(f"{ロール.mention}\n", "").replace(f"{ロール.mention}", "")

            new_embed = embed.copy()
            new_embed.set_field_at(0, name=embed.fields[0].name, value=field_value, inline=embed.fields[0].inline)

            await ロールパネルのid_.edit(view=view, embeds=[new_embed])

            await ctx.reply(embed=discord.Embed(title="編集しました。", color=discord.Color.green()), ephemeral=True)
            return
        else:
            pass
        await ロールパネルのid_.edit(view=view)
        await ctx.reply(embed=discord.Embed(title="編集しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="新しいGUIのロールパネルを作成します。", name="newgui-rolepanel")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_newgui_rolepanel(self, ctx: commands.Context, タイトル: str, ロール1: discord.Role, ロール2: discord.Role = None, ロール3: discord.Role = None, ロール4: discord.Role = None, ロール5: discord.Role = None, 説明: str = None):
        await ctx.defer(ephemeral=True)
        cont = container.Container(self.bot)
        cont.add_view(cont.text(f"# {タイトル}"))
        if 説明:
            cont.add_view(cont.text(f"{説明}"))
        b1 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール1.id}", style=1)
        cont.add_view(cont.labeled_button(f"{ロール1.name} ({ロール1.id})", b1))
        if ロール2:
            b2 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール2.id}", style=1)
            cont.add_view(cont.labeled_button(f"{ロール2.name} ({ロール2.id})", b2))
        if ロール3:
            b3 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール3.id}", style=1)
            cont.add_view(cont.labeled_button(f"{ロール3.name} ({ロール3.id})", b3))
        if ロール4:
            b4 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール4.id}", style=1)
            cont.add_view(cont.labeled_button(f"{ロール4.name} ({ロール4.id})", b4))
        if ロール5:
            b5 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール5.id}", style=1)
            cont.add_view(cont.labeled_button(f"{ロール5.name} ({ロール5.id})", b5))
        await cont.send(ctx.channel.id)
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="新しいGUIのロールパネルを編集します。", name="newgui-role-edit")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    @discord.app_commands.choices(
        削除か追加か=[
            discord.app_commands.Choice(name="追加", value="add"),
            discord.app_commands.Choice(name="削除", value="remove"),
            discord.app_commands.Choice(name="デバッグ", value="debug"),
        ]
    )
    async def panel_newgui_rolepanel_edit(self, ctx: commands.Context, メッセージ: discord.Message, ロール: discord.Role, 削除か追加か: discord.app_commands.Choice[str]):
        await ctx.defer(ephemeral=True)
        cont = container.Container(self.bot)
        con = await cont.fetch(メッセージ, ctx.channel.id)
        cont.comp = con[0].get("components", [])
        if 削除か追加か.name == "デバッグ":
            if not ctx.author.id == 1335428061541437531:
                return await ctx.reply("オーナーのみ実行可能です。")
            await ctx.reply(f"{cont.comp}")
        elif 削除か追加か.name == "追加":
            b1 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール.id}", style=1)
            cont.add_view(cont.labeled_button(f"{ロール.name} ({ロール.id})", b1))
            await cont.edit(メッセージ, ctx.channel.id)
        elif 削除か追加か.name == "削除":
            ls = []
            b1 = cont.labeled_customid_button(button_label=f"取得", custom_id=f"rolepanel_v1+{ロール.id}", style=1)
            for c in cont.comp:
                if c.get("components", {}) == {}:
                    ls.append(c)
                    continue
                if c.get("type", 0) == 9:
                    if c.get("components", {})[0].get("content", None) == f"{ロール.name} ({ロール.id})":
                        continue
                    ls.append(c)
            cont.comp = ls
            await cont.edit(メッセージ, ctx.channel.id)
        await ctx.reply(f"{削除か追加か.name}しました。")

    @role_panel.command(description="絶対値を使った認証パネルを作ります。", name="abs-auth")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authbutton(self, ctx, タイトル: str, 説明: str, ロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"authpanel_v1+{ロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="ワンクリック認証パネルを作ります。", name="auth")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authbutton_onclick(self, ctx, タイトル: str, 説明: str, ロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"authpanel_v2+{ロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="認証したらロールが外れた後にロールが付くパネルを作ります。", name="auth-plus")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authbutton_plus(self, ctx, タイトル: str, 説明: str, ロール: discord.Role, 外すロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"authpanel_plus_v1+{ロール.id}+{外すロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="Web認証パネルを作ります。", name="webauth")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authboost(self, ctx, タイトル: str, 説明: str, ロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"boostauth+{ロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="認証パネルに必要なロールを設定します。", name="auth-reqrole")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    @discord.app_commands.autocomplete(認証パネルのid=message_autocomplete)
    async def panel_auth_reqrole(self, ctx: commands.Context, 認証パネルのid: str, 必要なロール: discord.Role = None):
        await ctx.defer(ephemeral=True)
        try:
            認証パネルのid_ = await ctx.channel.fetch_message(int(認証パネルのid))
        except:
            return await ctx.reply(embed=discord.Embed(title="メッセージが見つかりません", color=discord.Color.red()), ephemeral=True)
        if 必要なロール:
            db = self.bot.async_db["Main"].AuthReqRole
            await db.replace_one(
                {"Message": 認証パネルのid_.id}, 
                {"Message": 認証パネルのid_.id, "Role": 必要なロール.id}, 
                upsert=True
            )
            return await ctx.reply(embed=discord.Embed(title="必要なロールを設定しました。", color=discord.Color.green()))
        else:
            db = self.bot.async_db["Main"].AuthReqRole
            await db.delete_one(
                {"Message": 認証パネルのid_.id}
            )
            return await ctx.reply(embed=discord.Embed(title="必要なロールを無効化しました。", color=discord.Color.green()))

    @role_panel.command(description="投票パネルを作ります。", name="poll")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def panel_poll(self, ctx: commands.Context, タイトル: str, 選択肢1: str, 選択肢2: str = None, 選択肢3: str = None, 選択肢4: str = None, 選択肢5: str = None):
        await ctx.defer(ephemeral=True)
        if not 選択肢2 and not 選択肢3 and not 選択肢4 and not 選択肢5:
            msg_ = await ctx.channel.send(embed=discord.Embed(title=タイトル, description=選択肢1, color=discord.Color.blue()))
            await msg_.add_reaction("👍")
            await msg_.add_reaction("👎")
            if ctx.interaction:
                await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)
            else:
                await ctx.message.add_reaction("✅")
            return
        if not 選択肢3 and not 選択肢4 and not 選択肢5:
            msg_ = await ctx.channel.send(embed=discord.Embed(title=タイトル, description="A .. " + 選択肢1 + f"\nB .. {選択肢2}", color=discord.Color.blue()))
            await msg_.add_reaction("🇦")
            await msg_.add_reaction("🇧")
            if ctx.interaction:
                await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)
            else:
                await ctx.message.add_reaction("✅")
            return
        text = ""
        # view = discord.ui.View()
        # view.add_item(discord.ui.Button(label=f"{選択肢1}", custom_id=f"poll+{選択肢1}"))
        text += f"1 .. {選択肢1}\n"
        try:
            if 選択肢2 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢2}", custom_id=f"poll+{選択肢2}"))
                text += f"2 .. {選択肢2}\n"
        except:
            pass
        try:
            if 選択肢3 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢3}", custom_id=f"poll+{選択肢3}"))
                text += f"3 .. {選択肢3}\n"
        except:
            pass
        try:
            if 選択肢4 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢4}", custom_id=f"poll+{選択肢4}"))
                text += f"4 .. {選択肢4}\n"
        except:
            pass
        try:
            if 選択肢5 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢5}", custom_id=f"poll+{選択肢5}"))
                text += f"5 .. {選択肢5}"
        except:
            pass
        # view.add_item(discord.ui.Button(label=f"集計", custom_id=f"poll_done+{ctx.author.id}"))
        # await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{text}", color=discord.Color.green()), view=view)
        msg_ = await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{text}", color=discord.Color.blue()))
        await msg_.add_reaction("1️⃣")
        if 選択肢2 != None:
            await msg_.add_reaction("2️⃣")
        await asyncio.sleep(1)
        if 選択肢3 != None:
            await msg_.add_reaction("3️⃣")
        if 選択肢4 != None:
            await msg_.add_reaction("4️⃣")
        if 選択肢5 != None:
            await msg_.add_reaction("5️⃣")
        if ctx.interaction:
            await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.message.add_reaction("✅")

    def randstring(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    @role_panel.command(description="チケットパネルを作ります。", name="ticket")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_ticket(self, ctx, タイトル: str, 説明: str, カテゴリ: discord.CategoryChannel = None, 実績チャンネル: discord.TextChannel = None, メンションするロール: discord.Role = None):
        msg = await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="チケットを作成", custom_id=f"ticket_v1")))
        if カテゴリ:
            db = self.bot.async_db["Main"].TicketCategory
            await db.replace_one(
                {"Channel": カテゴリ.id, "Message": msg.id}, 
                {"Channel": カテゴリ.id, "Message": msg.id}, 
                upsert=True
            )
        if 実績チャンネル:
            db = self.bot.async_db["Main"].TicketProgress
            await db.replace_one(
                {"Channel": 実績チャンネル.id, "Message": msg.id}, 
                {"Channel": 実績チャンネル.id, "Message": msg.id}, 
                upsert=True
            )
        if メンションするロール:
            db = self.bot.async_db["Main"].TicketRole
            await db.replace_one(
                {"Role": メンションするロール.id, "Message": msg.id}, 
                {"Role": メンションするロール.id, "Message": msg.id}, 
                upsert=True
            )
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="新しいGUIのチケットパネルを作ります。", name="newgui-ticket")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_newgui_ticket(self, ctx: commands.Context, タイトル: str, 説明: str, カテゴリ: discord.CategoryChannel = None, 実績チャンネル: discord.TextChannel = None):
        await ctx.defer(ephemeral=True)
        data = [
                {
                    "type": 17,
                    "components": [
                        {
                            "type": 10,
                            "content": タイトル
                        },
                        {
                            "type": 9,
                            "components": [
                                {
                                "type": 10,
                                "content": f"{説明}:"
                                }
                            ],
                            "accessory": {
                                "type": 2,
                                "style": 4,
                                "label": "チケットを開く",
                                "custom_id": "ticket_v1"
                            }
                        },
                    ]
                }
        ]
        
        msg = await self.send_beta_view(ctx.channel.id, data)

        if カテゴリ:
            db = self.bot.async_db["Main"].TicketCategory
            await db.replace_one(
                {"Channel": カテゴリ.id, "Message": int(msg["id"])}, 
                {"Channel": カテゴリ.id, "Message": int(msg["id"])}, 
                upsert=True
            )

        if 実績チャンネル:
            db = self.bot.async_db["Main"].TicketProgress
            await db.replace_one(
                {"Channel": 実績チャンネル.id, "Message": msg.id}, 
                {"Channel": 実績チャンネル.id, "Message": msg.id}, 
                upsert=True
            )
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="Web上で会話をするチケットパネルを作ります。", name="web-ticket")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def web_panel_ticket(self, ctx, タイトル: str, 説明: str, チャンネル: discord.TextChannel):
        msg = await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="チケットを作成", custom_id=f"ticket_v2")))
        db = self.bot.async_db["Main"].TicketAlert
        await db.replace_one(
            {"Channel": チャンネル.id, "Message": msg.id}, 
            {"Channel": チャンネル.id, "Message": msg.id}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="一時テキストチャンネルパネルを作成します。", name="freechannel")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_freechannel(self, ctx, タイトル: str, 説明: str):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="チャンネルを作成", custom_id=f"freech_v1")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="異議申し立てパネルを作成します。", name="obj")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_obj(self, ctx):
        await ctx.channel.send(embed=discord.Embed(title="サーバーに異議申し立てをする", color=discord.Color.blue(), description="以下のボタンから異議申し立てができます。"), view=discord.ui.View().add_item(discord.ui.Button(label="異議申し立て", custom_id="obj+")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="様々な募集をします。", name="party")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def panel_party(self, ctx, 内容: str, 最大人数: int):
        if 最大人数 > 16:
            return await ctx.reply(embed=discord.Embed(title="15人まで可能です。", color=discord.Color.red()), ephemeral=True)
        await ctx.channel.send(embed=discord.Embed(title="募集", color=discord.Color.blue()).add_field(name="内容", value=内容, inline=False).add_field(name="最大人数", value=f"{最大人数}人").add_field(name="現在の参加人数", value=f"0人").add_field(name="参加者", value=f"まだいません。", inline=False), view=discord.ui.View().add_item(discord.ui.Button(label="参加する", custom_id="join_party+")))
        if ctx.interaction:
            await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.message.add_reaction("✅")

    @role_panel.command(description="一コメを取得します。", name="top")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def top(self, ctx: commands.Context):
        await ctx.defer()
        async for top in ctx.channel.history(limit=1, oldest_first=True):
            await ctx.reply(embed=discord.Embed(title="最初のコメント", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="アクセスする", url=top.jump_url)))
            return

    def extract_user_id(self,mention: str) -> int | None:
        print(mention)
        match = re.match(r"<@&!?(\d+)>", mention)
        return int(match.group(1)) if match else None

    def extract_role_mentions(self, text):
        role_mentions = re.findall(r'<@&(\d+)>', text)[0]
        return role_mentions

    @role_panel.command(description="ほかのBotからコピーします。", name="copy")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_copy(self, ctx: commands.Context, パネル: discord.Message):
        await ctx.defer(ephemeral=True)
        if パネル.author.id == 1316023730484281394:
            if not パネル.embeds:
                return await ctx.reply(ephemeral=True, content="移行できないパネルです。")
            else:
                if パネル.embeds[0].fields[0].name == "利用可能なロール":
                    li = []
                    for p in パネル.embeds[0].fields[0].value.split("\n"):
                        li.append(self.extract_user_id(p))
                    view = discord.ui.View()
                    for l in li:
                        view.add_item(discord.ui.Button(label=f"{ctx.guild.get_role(l).name}", custom_id=f"rolepanel_v1+{l}"))
                    await ctx.channel.send(embed=discord.Embed(title=f"{パネル.embeds[0].title}", color=discord.Color.green()).add_field(name="ロール一覧", value=パネル.embeds[0].fields[0].value), view=view)
                    await ctx.reply(f"移行しました。")
                else:
                    await ctx.reply(ephemeral=True, content="移行に失敗しました。")
        elif パネル.author.id == 462522669036732416:
            if not パネル.embeds:
                return await ctx.reply(ephemeral=True, content="移行できないパネルです。")
            else:
                if "パネル名" in パネル.embeds[0].title:
                    li = []
                    for p in パネル.embeds[0].description.split("\n")[1:]:
                        li.append(self.extract_user_id("".join(p.split(":")[1:]).replace(" ", "")))
                    view = discord.ui.View()
                    text = ""
                    for l in li:
                        view.add_item(discord.ui.Button(label=f"{ctx.guild.get_role(l).name}", custom_id=f"rolepanel_v1+{l}"))
                        text += f"{ctx.guild.get_role(l).mention}\n"
                    await ctx.channel.send(embed=discord.Embed(title=f"{パネル.embeds[0].title.replace("パネル名: ", "", 1)}", color=discord.Color.green()).add_field(name="ロール一覧", value=text), view=view)
                    await ctx.reply(f"移行しました。")
                else:
                    await ctx.reply(ephemeral=True, content="移行に失敗しました。")
        elif パネル.author.id == 981314695543783484:
            if not パネル.embeds:
                return await ctx.reply(ephemeral=True, content="移行できないパネルです。")
            else:
                li = []
                for p in パネル.embeds[0].description.split("\n"):
                    li.append(int(self.extract_role_mentions(p)))
                view = discord.ui.View()
                text = ""
                for l in li:
                    view.add_item(discord.ui.Button(label=f"{ctx.guild.get_role(l).name}", custom_id=f"rolepanel_v1+{l}"))
                    text += f"{ctx.guild.get_role(l).mention}\n"
                await ctx.channel.send(embed=discord.Embed(title=f"{パネル.embeds[0].title}", color=discord.Color.green()).add_field(name="ロール一覧", value=text), view=view)
                await ctx.reply(f"移行しました。")
        else:
            await ctx.reply("パネルの移行に対応していません。", ephemeral=True)

    async def check_ticket_cat(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].TicketCategory
        try:
            dbfind = await db.find_one({"Message": interaction.message.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            return dbfind["Channel"]
        return None
    
    async def check_ticket_alert(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].TicketAlert
        try:
            dbfind = await db.find_one({"Message": interaction.message.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            return self.bot.get_channel(dbfind["Channel"])
        return None

    async def check_guild_bed(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].RestoreBed
        try:
            dbfind = await db.find_one({"Guild": int_.guild.id, "User": int_.user.id}, {"_id": False})
        except:
            return False
        if not dbfind is None:
            return True
        return False
    
    async def check_ticket_progress_channel(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].TicketProgress
        try:
            dbfind = await db.find_one({"Message": int_.message.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            try:
                return self.bot.get_channel(dbfind.get("Channel"))
            except:
                return None
        return None
    
    async def check_ticket_progress_channel_end(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].TicketProgressTemp
        try:
            dbfind = await db.find_one({"Message": int_.message.id}, {"_id": False})
            await db.delete_many({"Author": dbfind.get("Author")})
        except:
            return None, None
        if not dbfind is None:
            try:
                return self.bot.get_channel(dbfind.get("Channel")), self.bot.get_user(dbfind.get("Author"))
            except:
                return None, None
        return None, None

    async def get_ticket_mention(self, message: discord.Message):
        db = self.bot.async_db["Main"].TicketRole
        try:
            dbfind = await db.find_one({"Message": message.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            try:
                return message.guild.get_role(dbfind.get("Role")).mention
            except:
                return
        return None
    
    async def get_auth_reqrole(self, message: discord.Message):
        db = self.bot.async_db["Main"].AuthReqRole
        try:
            dbfind = await db.find_one({"Message": message.id}, {"_id": False})
        except:
            return None
        if not dbfind is None:
            try:
                return message.guild.get_role(dbfind.get("Role"))
            except:
                return None
        return None

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "rolepanel_v1+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if not interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            await interaction.user.add_roles(interaction.guild.get_role(int(custom_id.split("+")[1])))
                            await interaction.followup.send("ロールを追加しました。", ephemeral=True)
                        else:
                            await interaction.user.remove_roles(interaction.guild.get_role(int(custom_id.split("+")[1])))
                            await interaction.followup.send("ロールを剥奪しました。", ephemeral=True)
                    except discord.Forbidden as f:
                        await interaction.followup.send("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.followup.send("追加に失敗しました。", ephemeral=True)
                elif "authpanel_v1+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if not r in interaction.user.roles:
                                return await interaction.response.send_message("あなたは指定されたロールを持っていないため、認証できません。", ephemeral=True)
                        if interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            return await interaction.response.send_message("あなたはすでに認証しています。", ephemeral=True)
                        await interaction.response.send_modal(AuthModal_keisan(interaction.guild.get_role(int(custom_id.split("+")[1]))))
                    except discord.Forbidden as f:
                        await interaction.response.send_message("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.response.send_message("認証に失敗しました。", ephemeral=True)
                elif "authpanel_v2+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if not r in interaction.user.roles:
                                return await interaction.response.send_message("あなたは指定されたロールを持っていないため、認証できません。", ephemeral=True)
                        if interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            return await interaction.response.send_message("あなたはすでに認証しています。", ephemeral=True)
                        await interaction.response.defer(ephemeral=True)
                        await interaction.user.add_roles(interaction.guild.get_role(int(custom_id.split("+")[1])))
                        await interaction.followup.send("認証が完了しました。", ephemeral=True)
                    except discord.Forbidden as f:
                        await interaction.response.send_message("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.response.send_message("認証に失敗しました。", ephemeral=True)
                elif "authpanel_plus_v1+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if not r in interaction.user.roles:
                                return await interaction.response.send_message("あなたは指定されたロールを持っていないため、認証できません。", ephemeral=True)
                        if interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            return await interaction.response.send_message("あなたはすでに認証しています。", ephemeral=True)
                        await interaction.response.send_modal(PlusAuthModal_keisan(interaction.guild.get_role(int(custom_id.split("+")[1])), interaction.guild.get_role(int(custom_id.split("+")[2]))))
                    except discord.Forbidden as f:
                        await interaction.response.send_message("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.response.send_message(f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "poll+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        des = interaction.message.embeds[0].description.split("\n")
                        text = ""
                        for d in des:
                            if d.split(": ")[0] == custom_id.split("+")[1]:
                                ct = int(d.split(": ")[1]) + 1
                                text += f"{d.split(": ")[0]}: {ct}\n"
                                continue
                            text += f"{d}\n"
                        await interaction.message.edit(embed=discord.Embed(title=f"{interaction.message.embeds[0].title}", description=f"{text}", color=discord.Color.green()))
                        await interaction.followup.send(content="投票しました。", ephemeral=True)
                    except:
                        await interaction.followup.send(f"投票に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "poll_done" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if custom_id.split("+")[1] == f"{interaction.user.id}":
                            await interaction.message.edit(view=None)
                            await interaction.followup.send(content="集計しました。", ephemeral=True)
                        else:
                            await interaction.followup.send(content="権限がありません。", ephemeral=True)
                    except:
                        await interaction.followup.send(f"集計に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "ticket_v1" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        overwrites = {
                            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        }
                        check_c = await self.check_ticket_cat(interaction)
                        current_time = time.time()
                        last_message_time = tku_cooldown.get(interaction.user.id, 0)
                        if current_time - last_message_time < 180:
                            return await interaction.followup.send(f"レートリミットです。", ephemeral=True)
                        tku_cooldown[interaction.user.id] = current_time
                        db_progress = self.bot.async_db["Main"].TicketProgressTemp
                        ch = await self.check_ticket_progress_channel(interaction)
                        role_ment = await self.get_ticket_mention(interaction.message)
                        if not check_c:
                            if interaction.channel.category:
                                tkc = await interaction.channel.category.create_text_channel(name=f"{interaction.user.name}-ticket", overwrites=overwrites)
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="閉じる", custom_id="delete_ticket", style=discord.ButtonStyle.red))
                                msg = await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`のチケット", color=discord.Color.green()), view=view, content=role_ment if role_ment else f"{interaction.user.mention}")
                                if ch:
                                    await db_progress.replace_one(
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        upsert=True
                                    )
                                await interaction.followup.send(f"チケットを作成しました。\n{tkc.jump_url}", ephemeral=True)
                            else:
                                tkc = await interaction.guild.create_text_channel(name=f"{interaction.user.name}-ticket", overwrites=overwrites)
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="閉じる", custom_id="delete_ticket", style=discord.ButtonStyle.red))
                                msg = await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`のチケット", color=discord.Color.green()), view=view, content=role_ment if role_ment else f"{interaction.user.mention}")
                                if ch:
                                    await db_progress.replace_one(
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        upsert=True
                                    )
                                await interaction.followup.send(f"チケットを作成しました。\n{tkc.jump_url}", ephemeral=True)
                        else:
                            if self.bot.get_channel(check_c):
                                tkc = await self.bot.get_channel(check_c).create_text_channel(name=f"{interaction.user.name}-ticket", overwrites=overwrites)
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="閉じる", custom_id="delete_ticket", style=discord.ButtonStyle.red))
                                msg = await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`のチケット", color=discord.Color.green()), view=view, content=role_ment if role_ment else f"{interaction.user.mention}")
                                if ch:
                                    await db_progress.replace_one(
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        {"Channel": ch.id, "Message": msg.id, "Author": interaction.user.id}, 
                                        upsert=True
                                    )
                                await interaction.followup.send(f"チケットを作成しました。\n{tkc.jump_url}", ephemeral=True)
                            else:
                                await interaction.followup.send("エラーが発生しました。\n指定されたカテゴリが見つかりません。", ephemeral=True)
                    except:
                        await interaction.followup.send(f"チケット作成に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "ticket_v2" in custom_id:
                    await interaction.response.defer(ephemeral=True)
                    current_time = time.time()
                    last_message_time = tku_cooldown.get(interaction.user.id, 0)
                    if current_time - last_message_time < 180:
                        return await interaction.followup.send(f"レートリミットです。", ephemeral=True)
                    tku_cooldown[interaction.user.id] = current_time
                    channel = await self.check_ticket_alert(interaction)
                    if not channel:
                        return await interaction.followup.send(ephemeral=True, content="チケット作成に失敗しました。")
                    loop = asyncio.get_event_loop()
                    cha = await loop.run_in_executor(None, partial(Chaat))
                    await loop.run_in_executor(None, partial(cha.login))
                    room = await loop.run_in_executor(None, partial(cha.create_room))
                    await loop.run_in_executor(None, partial(cha.send_room, f"{interaction.guild.name}のチケットへようこそ！", room["hash"]))
                    await loop.run_in_executor(None, partial(cha.send_room, f"{interaction.user.name}さん、よろしく！", room["hash"]))
                    await channel.send(embed=discord.Embed(title="チケットが開かれました！", description=f"https://c.kuku.lu/{room["hash"]}\nにアクセスして、対応してください。", color=discord.Color.blue()), view=discord.ui.View().add_item(discord.ui.Button(label="対応する", url=f"https://c.kuku.lu/{room["hash"]}")))
                    await interaction.followup.send(ephemeral=True, content=f"https://c.kuku.lu/{room["hash"]}\n上のURLにアクセスしてください。")
                elif "delete_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        ch, user = await self.check_ticket_progress_channel_end(interaction)
                        try:
                            h = []
                            async for his in interaction.channel.history(limit=100, oldest_first=True):
                                h.append(f"{his.author.name}: {his.content.replace("\n", "\\n")}")
                            kaiwa_io = io.StringIO("\n".join(h))
                            if not user:
                                await ch.send(embed=discord.Embed(title="チケットの実績が記録されました", color=discord.Color.green()).add_field(name="チケットを開いた人", value="不明").set_thumbnail(url=self.bot.user.default_avatar.url), file=discord.File(kaiwa_io, "hist.txt"))
                            else:
                                await ch.send(embed=discord.Embed(title="チケットの実績が記録されました", color=discord.Color.green()).add_field(name="チケットを開いた人", value=f"{user.mention}\n({user.id})").set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url), file=discord.File(kaiwa_io, "hist.txt"))
                            kaiwa_io.close()
                        except:
                            pass
                        await interaction.channel.delete()
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "freech_v1" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if f"{interaction.user.id}" in freech:
                            return await interaction.followup.send(f"複数部屋は作成できません。", ephemeral=True)
                        if interaction.channel.category:
                            tkc = await interaction.channel.category.create_text_channel(name=f"{interaction.user.name}の部屋", overwrites=interaction.channel.category.overwrites)
                        else:
                            tkc = await interaction.guild.create_text_channel(name=f"{interaction.user.name}の部屋")
                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="削除", custom_id="freech_ticket", style=discord.ButtonStyle.red))
                        await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`の部屋", color=discord.Color.green()), view=view)
                        freech.append(f"{interaction.user.id}")
                        await interaction.followup.send(f"部屋を作成しました。\n{tkc.jump_url}", ephemeral=True)
                    except:
                        await interaction.followup.send(f"部屋作成に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "freech_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        try:
                            freech.remove(f"{interaction.user.id}")
                        except:
                            pass
                        await interaction.channel.delete()
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "boostauth+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if not r in interaction.user.roles:
                                return await interaction.followup.send("あなたは指定されたロールを持っていないため、認証できません。", ephemeral=True)
                        role = custom_id.split("+")[1]
                        code = self.randstring(30)
                        db = self.bot.async_db["Main"].MemberAddAuthRole
                        await db.replace_one(
                            {"Guild": str(interaction.guild.id), "Code": code}, 
                            {"Guild": str(interaction.guild.id), "Code": code, "Role": role}, 
                            upsert=True
                        )
                        await interaction.followup.send("この認証パネルは、Webにアクセスする必要があります。\n以下のボタンからアクセスして認証してください。\n\n追記: あなたの参加しているサーバーが取得されます。\nそれらの情報は、Botの動作向上のために使用されます。", ephemeral=True, view=discord.ui.View().add_item(discord.ui.Button(label="認証する", url=f"https://discord.com/oauth2/authorize?client_id=1322100616369147924&response_type=code&redirect_uri=https%3A%2F%2Fwww.sharkbot.xyz%2Finvite_auth&scope=identify+guilds+connections&state={code}")))
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "postauth+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        role = custom_id.split("+")[1]
                        code = self.randstring(30)
                        db = self.bot.async_db["Main"].PostAuth
                        await db.replace_one(
                            {"Guild": str(interaction.guild.id), "Code": code}, 
                            {"Guild": str(interaction.guild.id), "Code": code, "Role": role, "User": str(interaction.user.id)}, 
                            upsert=True
                        )
                        await interaction.followup.send("認証をするには、\n```{'code': 'code_', 'guild': 'guild_'}```\nを`https://www.sharkbot.xyz/postauth`\nにPostしてください。".replace("code_", code).replace("guild_", str(interaction.guild.id)), ephemeral=True)
                    except:
                        await interaction.followup.send(f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "obj+" in custom_id:
                    try:
                        await interaction.response.send_modal(ObjModal())
                    except:
                        await interaction.response.send_message(f"異議申し立てに失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "obj_ok+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        gid = custom_id.split("+")[1]
                        uid = custom_id.split("+")[2]
                        guild = self.bot.get_guild(int(gid))
                        db = self.bot.async_db["Main"].ObjReq
                        await db.delete_one({"Guild": guild.id, "User": int(uid)})
                        await self.bot.get_user(int(uid)).send(f"「{guild.name}」の異議申し立てが受諾されました。")
                        await interaction.followup.send(ephemeral=True, content="異議申し立てに返信しました。")
                    except:
                        await interaction.followup.send(f"異議申し立てに失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "obj_no+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        gid = custom_id.split("+")[1]
                        uid = custom_id.split("+")[2]
                        guild = self.bot.get_guild(int(gid))
                        db = self.bot.async_db["Main"].ObjReq
                        await db.delete_one({"Guild": guild.id, "User": int(uid)})
                        await self.bot.get_user(int(uid)).send(f"「{guild.name}」の異議申し立てが拒否されました。")
                        await interaction.followup.send(ephemeral=True, content="異議申し立てに返信しました。")
                    except:
                        await interaction.followup.send(f"異議申し立てに失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "botban+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        type_ = interaction.message.embeds[0].fields[0].value
                        if type_ == "ユーザー":
                            target = self.bot.get_user(int(interaction.message.embeds[0].footer.text))
                            db = self.bot.async_db["Main"].BlockUser
                            await db.replace_one(
                                {"User": target.id}, 
                                {"User": target.id}, 
                                upsert=True
                            )
                        elif type_ == "サーバー":
                            target = self.bot.get_guild(int(interaction.message.embeds[0].footer.text))
                            db = self.bot.async_db["Main"].BlockGuild
                            await db.replace_one(
                                {"Guild": target.id}, 
                                {"Guild": target.id}, 
                                upsert=True
                            )
                        await interaction.message.reply("BotからBANしました。")
                        await interaction.followup.send(ephemeral=True, content=f"BotからBANしました。\nID: {target.id}\nタイプ: {type_}")
                    except:
                        await interaction.followup.send(f"BotからのBANに失敗しました。", ephemeral=True)
                elif "botwarn+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        type_ = interaction.message.embeds[0].fields[0].value
                        if type_ == "ユーザー":
                            target = self.bot.get_user(int(interaction.message.embeds[0].footer.text))
                            reason = interaction.message.embeds[0].fields[2].value
                            await target.send(embed=discord.Embed(title="SharkBotからあなたは警告されました。", color=discord.Color.yellow()).add_field(name="理由", value=reason))
                        elif type_ == "サーバー":
                            target = self.bot.get_guild(int(interaction.message.embeds[0].footer.text))
                            reason = interaction.message.embeds[0].fields[2].value
                            await target.owner.send(embed=discord.Embed(title="SharkBotからあなたは警告されました。", color=discord.Color.yellow()).add_field(name="理由", value=reason))
                        await interaction.message.reply("警告しました。")
                        await interaction.followup.send(ephemeral=True, content=f"Botから警告しました。\nID: {target.id}\nタイプ: {type_}")
                    except:
                        await interaction.followup.send(f"Botからの警告に失敗しました。", ephemeral=True)
                elif "botdelete+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        await interaction.message.reply("破棄しました。")
                        await interaction.followup.send(ephemeral=True, content=f"破棄しました。")
                    except:
                        await interaction.followup.send(f"破棄に失敗しました。", ephemeral=True)
                elif "join_party+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if f"{interaction.user.id}" in interaction.message.embeds[0].fields[3].value:
                            return
                        max_memb = int(interaction.message.embeds[0].fields[1].value.replace("人", ""))
                        memb = int(interaction.message.embeds[0].fields[2].value.replace("人", ""))
                        emb = interaction.message.embeds[0].copy()
                        emb.set_field_at(2, name="現在の参加人数", value=f"{memb + 1}人", inline=True)
                        if interaction.message.embeds[0].fields[3].value == "まだいません。":
                            emb.set_field_at(3, name="参加者", value=f"{interaction.user.display_name} ({interaction.user.id})", inline=False)
                        else:
                            emb.set_field_at(3, name="参加者", value=f"{interaction.message.embeds[0].fields[3].value}\n{interaction.user.display_name} ({interaction.user.id})", inline=False)
                        if int(interaction.message.embeds[0].fields[2].value.replace("人", "")) == max_memb:
                            await interaction.message.edit(embeds=[emb, discord.Embed(title="募集が完了しました。", color=discord.Color.red())], view=None)
                        else:
                            await interaction.message.edit(embed=emb)
                        await interaction.followup.send(ephemeral=True, content=f"参加しました。")
                    except Exception as e:
                        await interaction.message.edit(embed=discord.Embed(title="エラーが発生したため、強制終了しました。", color=discord.Color.red()))
                        await interaction.followup.send(f"参加に失敗しました。\nエラーコード: {e}", ephemeral=True)
                elif "viproom+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        role = custom_id.split("+")[1]
                        if not self.bot.get_guild(1343124570131009579).get_member(interaction.user.id):
                            return await interaction.followup.send(ephemeral=True, content=f"VIPルームに参加する権限がありません。\nSharkBotサポートサーバーに参加して下さい。")
                        if self.bot.get_guild(1343124570131009579).get_role(1359843498395959437) in self.bot.get_guild(1343124570131009579).get_member(interaction.user.id).roles:
                            await interaction.user.add_roles(interaction.guild.get_role(int(role)))
                        else:
                            return await interaction.followup.send(ephemeral=True, content=f"VIPルームに参加する権限がありません。\nVIPルーム権限を購入して下さい。")
                        await interaction.followup.send(ephemeral=True, content=f"VIPルームに参加しました。")
                    except:
                        await interaction.followup.send(f"VIPルームに参加できませんでした。", ephemeral=True)
        except:
            return


    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_betapanel(self, interaction: discord.Interaction):
        try:
            if not interaction.data['component_type'] == 2:
                return
            try:
                custom_id = interaction.data["custom_id"]
            except:
                return
            if "test_beta_view_button" in custom_id:
                await interaction.response.send_message("OK!", ephemeral=True)
        except:
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
                            "content": "これはテストビューです"
                        },
                        {
                            "type": 9,
                            "components": [
                                {
                                "type": 10,
                                "content": "URLです:"
                                }
                            ],
                            "accessory": {
                                "type": 2,
                                "style": 5,
                                "label": "Reference",
                                "url": "https://discord.com/developers/docs/components/reference#what-is-a-component-component-types"
                            }
                        },
                        {
                            "type": 9,
                            "components": [
                                {
                                "type": 10,
                                "content": "ボタンです:"
                                }
                            ],
                            "accessory": {
                                "type": 2,
                                "style": 4,
                                "label": "テストボタン",
                                "custom_id": "test_beta_view_button"
                            }
                        },
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.text()

    @commands.command(name="beta_panel")
    async def beta_panel(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await self.send_raw_interaction(ctx.channel.id)

async def setup(bot):
    await bot.add_cog(PanelCog(bot))