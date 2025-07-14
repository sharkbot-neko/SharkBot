from discord.ext import commands, oauth2
import discord
import traceback
import sys
from deep_translator import GoogleTranslator
import logging
import urllib
import datetime
import random, string
import asyncio
from bs4 import BeautifulSoup
from collections import defaultdict
from functools import partial
import aiohttp
import requests
import MeCab
from aiohttp import ClientSession
import re
from discord import Webhook
import time
import json
from discord import app_commands

def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)


COOLDOWN_TIME_KEIGO = 5
cooldown_keigo_time = {}
COOLDOWN_TIME_TRANS = 3
cooldown_trans_time = {}
COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}
cooldown_auto_protect_time = {}
cooldown_auto_translate = {}

ratelimit_search = {}

cooldown_sharkass = {}

cooldown_pets = {}

cooldown_check_url = {}

cooldown_engonly = {}

cooldown_disable_command = {}

cooldown_sharkbot_mention = {}

URL_REGEX = re.compile(r"https://discord.com/channels/(\d+)/(\d+)/(\d+)")

message_counts = defaultdict(int)
spam_threshold = 3
time_window = 5

message_counts_userapp = defaultdict(int)

class FunctionDisabled(commands.CommandError):
    pass

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

class Login:
    def __init__(self, school_code, login_id, password):
        self.session = requests.Session()

        response = self.session.get('https://ela.education.ne.jp/students')
        bs = BeautifulSoup(response.text, 'html.parser')

        token_input = bs.find("input", {"name": "_token"})
        if not token_input:
            raise ValueError("CSRFトークンが見つかりませんでした。")

        self.token = token_input["value"]

        data = {
            '_token': self.token,
            'school_code': school_code,
            'login_id': login_id,
            'password': password,
            'is_keep': '1',
        }

        response = self.session.post('https://ela.education.ne.jp/students/top/login', data=data)

        if response.url == 'https://ela.education.ne.jp/students/top/login':
            raise ValueError("ログインに失敗しました。IDやパスワードを確認してください。")
        
    def login(self):
        return self.session

class User:
    def __init__(self, session):
        self.html = session.get('https://ela.education.ne.jp/students/home').text
        bs = BeautifulSoup(self.html, 'html.parser')

        article = bs.find("article", class_="login-name")
        if not article:
            raise ValueError("ユーザー情報が見つかりませんでした。")

        name_elements = article.find_all("dd")

        if len(name_elements) < 5:
            raise ValueError("ユーザー情報の取得に失敗しました。")

        self.school_name = name_elements[0].get_text(strip=True)
        self.school_learn = name_elements[1].get_text(strip=True)
        self.school_set = name_elements[2].get_text(strip=True)
        self.school_number = name_elements[3].get_text(strip=True)
        self.name = name_elements[4].get_text(strip=True)

class WebAuthToken:
    def __init__(self, session, drill_id: int, sequence: int):
        params = {
            'start_mode': '2',
            'user_student_drill_id': f'{drill_id}',
            'history_type': '1',
            'sequence': str(sequence),
        }
        self.html = session.get(f'https://ela.education.ne.jp/students/questions/question/1', params=params).text
        soup = BeautifulSoup(self.html, "html.parser")
        script_tag = soup.find_all("script")
        if script_tag:
            for s in script_tag:
                try:
                    match = re.search(r"var data = (\{.*?\});", s.string, re.DOTALL)
                except:
                    continue
                if match:
                    json_data = json.loads(match.group(1))
                    self.json = json_data
                    self.token = self.json["href"]["api_token"]
                    self.user_id = self.json["href"]["api_user_id"]
                    return
                
        print("見つかりませんでした")
                
class Answer:
    def __init__(self, json: dict):
        self.api_json = json
        self.answers = json["question"]["answer_groups"]
        self.user_student_questions = json["user_student_questions"]["1"]["user_student_drill_id"]
        self.json = {}
        for key, value in self.answers.items():
            pat = value["patterns"]
            for p in pat:
                ans = p["answer_ids"]
                for k, v in ans.items():
                    self.json[k] = [v]
        self.all_q = len(json["user_student_questions"])

    def judge(self, sequence: int, userid: str, ans: dict, token: str, session):
        jso = self.api_json["question"]["answers"]["1"]["type"]
        new_ans = {}
        for k, v in ans.items():
            str_k = str(k)
            if jso == 1:
                if isinstance(v, list):
                    new_ans[str_k] = v
                else:
                    new_ans[str_k] = [v]
            elif jso == 2:
                if isinstance(v, (list, tuple, set)):
                    new_ans[str_k] = "".join(map(str, v))
                else:
                    new_ans[str_k] = str(v)
            elif jso == 3:
                new_ans[str_k] = str(v)

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://ela.education.ne.jp',
            'priority': 'u=1, i',
            'referer': f'https://ela.education.ne.jp/students/questions/question/1?start_mode=2&user_student_drill_id={self.user_student_questions}&history_type=1&sequence={sequence}',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action_mode': '1',
            'history_type': '1',
            'is_unknown': '0',
            'user_student_drill_id': str(self.user_student_questions),
            'sequence': str(sequence),
            'answers': urllib.parse.quote(json.dumps(new_ans)),
            'memo': '',
            'auth_type': '1',
            'user_id': userid,
            'token': token,
        }

        response = session.post('https://ela.education.ne.jp/api/questions/judge', data=data, headers=headers)

        return response.json()["data"]["correct"]
    
    def results(self, session):
        params = {
            'action_mode': '1',
            'history_type': '1',
            'user_student_drill_id': str(self.user_student_questions),
        }

        response = session.get('https://ela.education.ne.jp/students/questions/results', params=params)

        return True

class SettingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.token_backup = self.tkj["Token"]
        self.tagger = MeCab.Tagger()
        print(f"init -> SettingCog")

        bot.add_check(self.ban_user_block)
        bot.add_check(self.ban_guild_block)
        bot.add_check(self.disable_function)

    def cog_unload(self):
        self.bot.remove_check(self.ban_user_block)
        self.bot.remove_check(self.ban_guild_block)
        self.bot.remove_check(self.disable_function)

    async def is_command_enabled(self, guild_id, command_name):
        doc = await self.bot.async_db["Main"].CommandSetting.find_one({"guild_id": guild_id})
        if doc and "disabled_commands" in doc:
            return command_name not in doc["disabled_commands"]
        return True

    async def search_message(self, search_word: str, message: discord.Message):
        try:
            await message.add_reaction("🔎")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Google検索", url=f"https://www.google.com/search?q={search_word.replace(" ", "+").replace("\n", "+")}"))
            for m in message.guild.roles:
                if search_word in m.name:
                    await message.reply(embed=discord.Embed(title=f"{search_word}の検索結果です。", color=discord.Color.blue()).add_field(name="ロール名", value=f"{m.name}", inline=False).add_field(name="ロールID", value=f"{m.id}", inline=False).add_field(name="もしかして。。？", value=f"{m.name}", inline=False), view=view)
                    return
            for m in message.guild.channels:
                if search_word in m.name:
                    await message.reply(embed=discord.Embed(title=f"{search_word}の検索結果です。", color=discord.Color.blue()).add_field(name="チャンネル名", value=f"{m.name}", inline=False).add_field(name="チャンネルID", value=f"{m.id}", inline=False).add_field(name="もしかして。。？", value=f"{m.name}", inline=False).add_field(name="飛ぶ", value=f"{m.jump_url}"), view=view)
                    return
            for m in message.guild.members:
                if search_word in m.display_name:
                    await message.reply(embed=discord.Embed(title=f"{search_word}の検索結果です。", color=discord.Color.blue()).add_field(name="ユーザー名", value=f"{m.name}", inline=False).add_field(name="ユーザーID", value=f"{m.id}", inline=False).add_field(name="もしかして。。？", value=f"{m.display_name}", inline=False).set_thumbnail(url=m.avatar.url if m.avatar else m.default_avatar.url), view=view)
                    return
            return await message.reply(embed=discord.Embed(title="Google検索結果です。", description=f"[リンクを開く](https://www.google.com/search?q={search_word.replace(" ", "+").replace("\n", "+")})", color=discord.Color.green()), view=view)
        except Exception as e:
            return

    async def ban_user_block(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": ctx.author.id}, {"_id": False})
        except:
            return True
        if not dbfind is None:
            return False
        return True
    
    async def ban_guild_block(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].BlockGuild
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return True
        if not dbfind is None:
            return False
        return True
    
    @commands.Cog.listener("on_message")
    async def on_message_translate_auto(self, message: discord.Message):
        if message.author.bot:
            return
        
        db = self.bot.async_db["Main"].AutoTranslate

        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_auto_translate.get(message.channel.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_auto_translate[message.channel.id] = current_time

        translator = GoogleTranslator(source="auto", target=dbfind.get("Lang", "en"))
        translated_text = translator.translate(message.content)

        embed = discord.Embed(
            title=f"<:Success:1362271281302601749> 翻訳 ({dbfind.get("Lang", "en")} へ)",
            description=f"{translated_text}",
            color=discord.Color.green()
        ).set_footer(text="Google Translate")

        await message.reply(embed=embed)

    @commands.Cog.listener("on_message")
    async def on_message_sharkbot_mention(self, message: discord.Message):
        if message.author.bot:
            return
        
        if message.mentions == []:
            return
        
        current_time = time.time()
        last_message_time = cooldown_sharkbot_mention.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_sharkbot_mention[message.guild.id] = current_time

        for men in message.mentions:
            if not men.id == self.bot.user.id:
                continue

            if message.content.endswith("を調べて"):
                search_word = message.content.split("を調べて")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("ってなに？"):
                search_word = message.content.split("ってなに？")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("とは"):
                search_word = message.content.split("とは")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("とは？"):
                search_word = message.content.split("とは？")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("ってなんだ？"):
                search_word = message.content.split("ってなんだ？")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("を教えて"):
                search_word = message.content.split("を教えて")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("を検索して"):
                search_word = message.content.split("を検索して")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if message.content.endswith("を検索して"):
                search_word = message.content.split("を検索して")[0]
                return await self.search_message(search_word.replace(f"{self.bot.user.mention}", "").replace(" ", ""), message)
            if "固定" in message.content:
                return await message.reply("固定メッセージは、\n固定したいメッセージを送った後、右クリックからアプリ -> メッセージ固定\nで固定できます。")
            if "gc" in message.content.lower():
                return await message.reply("グローバルチャットは、\n`/globalchat`で参加できます。\n参加にはメンバーが20人以上必要です。")
            if "globalchat" in message.content.lower():
                return await message.reply("グローバルチャットは、\n`/globalchat`で参加できます。\n参加にはメンバーが20人以上必要です。")
            if "グローバルチャット" in message.content.lower():
                return await message.reply("グローバルチャットは、\n`/globalchat`で参加できます。\n参加にはメンバーが20人以上必要です。")
            return

    @commands.Cog.listener("on_command_error")
    async def on_command_error_functiondisabled(self, ctx: commands.Context, error):
        if isinstance(error, FunctionDisabled):
            current_time = time.time()
            last_message_time = cooldown_engonly.get(ctx.guild.id, 0)
            if current_time - last_message_time < 5:
                a = None
                return a
            cooldown_engonly[ctx.guild.id] = current_time
            return await ctx.reply(embed=discord.Embed(title="そのコマンドは無効化されています。", color=discord.Color.red(), description="サーバー管理者に問い合わせてください。"), ephemeral=True)

    async def disable_function(self, ctx: commands.Context):
        if ctx.guild is None:
            return True

        guild_id = ctx.guild.id
        full_command = ctx.command.qualified_name

        db = self.bot.async_db["Main"].CommandSetting

        doc = await db.find_one({"guild_id": guild_id})
        disabled_commands = doc.get("disabled_commands", []) if doc else []

        if full_command in disabled_commands:
            raise FunctionDisabled


        """
        try:

            root_parent = ctx.command.root_parent
            if root_parent:
                cmd = self.bot.get_command(root_parent.qualified_name)
                if isinstance(cmd, commands.HybridGroup) and cmd.fallback:
                    if cmd.fallback == cmd.name.split(" ")[1]:
                        
                        fallback_command = f"{cmd.name} {cmd.fallback}"
                        if fallback_command in disabled_commands:
                            raise FunctionDisabled
        except:
            print(f"{sys.exc_info()}")
            pass
        """

        parent = ctx.command.parent
        while parent:
            if parent.qualified_name in disabled_commands:
                raise FunctionDisabled
            parent = parent.parent

        return True

    async def return_setting(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        return True
    
    async def return_text(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return "標準"
        if dbfind is None:
            return "標準"
        return dbfind

    async def return_bool(self, tf: bool):
        if tf:
            return "<:ON:1333716076244238379>"
        return "<:OFF:1333716084364279838>"

    async def keigo_trans(self, kougo_text):
        request_data = {
                "kougo_writing": kougo_text,
                "mode": "direct",
                "platform": 0,
                "translation_id": ""
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://y026dvhch0.execute-api.ap-northeast-1.amazonaws.com/translate", json=request_data) as response:
                    if response.status != 200:
                        return "Error"
                    response_data = await response.json()
                    return response_data.get("content", "敬語に変換できませんでした。")

        except aiohttp.ClientError as e:
            return f"Network error occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    @commands.Cog.listener("on_message")
    async def on_message_command(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author == self.bot.user:
            return

        await self.bot.process_commands(message)
        return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_stickrole(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].StickRole
        try:
            dbfind = await db.find_one({"Guild": g.id, "User": member.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            r = member.guild.get_role(dbfind["Role"])
            await member.add_roles(r)
        except:
            return
    
    @commands.Cog.listener("on_message")
    async def on_message_filedeletor(self, message: discord.Message):
        if message.author.bot:
            return
        if message.attachments == []:
            return
        if not message.guild:
            return
        if message.author.guild_permissions.administrator:
            return
        db = self.bot.async_db["Main"].FileAutoDeletor
        try:
            dbfind = await db.find_one({"guild_id": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        check = dbfind.get("end", None)
        if not check:
            return
        for at in message.attachments:
            for c in check:
                if at.filename.endswith(f"{c}"):
                    try:
                        await message.author.timeout(datetime.timedelta(minutes=3))
                        await message.delete()
                    except:
                        return
                    return

    @commands.Cog.listener("on_message")
    async def on_message_englishonly(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].EnglishOnlyChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_engonly.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_engonly[message.guild.id] = current_time
        try:
            if re.match(r"^[A-Za-z\s.,!?\"'()\-:;]+$", message.content):
                return
            else:
                await message.delete()
        except:
            return

    @commands.Cog.listener("on_voice_state_update")
    async def on_voice_state_update_datetime(self, member, before, after):
        return
        if after.channel is not None:
            voice_channel = after.channel
            db = self.bot.async_db["Main"].VoiceTime
            try:
                dbfind = await db.find_one({"Channel": voice_channel.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            now = datetime.datetime.now()
            try:
                n = voice_channel.name.split("-")[0]
                await voice_channel.edit(name=f"{n}-{now.strftime("%m_%d_%H_%M_%S")}")
            except:
                n = voice_channel.name
                await voice_channel.edit(name=f"{n}-{now.strftime("%m_%d_%H_%M_%S")}")

    async def get_score_warn(self, guild: discord.Guild, score: int):
        db = self.bot.async_db["Main"].WarnScoreSetting
        try:
            dbfind = await db.find_one({"Guild": guild.id, "Score": score}, {"_id": False})
            return dbfind["Setting"]
        except:
            return 0

    def return_warn_text(self, sc: int):
        if sc == 0:
            return "🤐タイムアウト3分"
        elif sc == 1:
            return "🤐タイムアウト5分"
        elif sc == 2:
            return "🤐タイムアウト10分"
        elif sc == 3:
            return "👢Kick"
        elif sc == 4:
            return "🔨BAN"
        elif sc == 5:
            return "❔なし"
        else:
            return "🤐タイムアウト3分"

    async def run_warn(self, score: int, message: discord.Message):
        sc = await self.get_score_warn(message.guild, score)
        if sc == 0:
            await message.author.timeout(datetime.timedelta(minutes=3))
        elif sc == 1:
            await message.author.timeout(datetime.timedelta(minutes=5))
        elif sc == 2:
            await message.author.timeout(datetime.timedelta(minutes=10))
        elif sc == 3:
            await message.author.kick()
        elif sc == 4:
            await message.author.ban()
        elif sc == 5:
            return
        else:
            await message.author.timeout(datetime.timedelta(minutes=3))

    async def run_warn_int_author(self, score: int, message: discord.Message, int_: discord.MessageInteractionMetadata):
        sc = await self.get_score_warn(message.guild, score)
        if sc == 0:
            await message.guild.get_member(int_.user.id).timeout(datetime.timedelta(minutes=3))
        elif sc == 1:
            await message.guild.get_member(int_.user.id).timeout(datetime.timedelta(minutes=5))
        elif sc == 2:
            await message.guild.get_member(int_.user.id).timeout(datetime.timedelta(minutes=10))
        elif sc == 3:
            await message.guild.get_member(int_.user.id).kick()
        elif sc == 4:
            await message.guild.get_member(int_.user.id).ban()
        elif sc == 5:
            return
        else:
            await message.guild.get_member(int_.user.id).timeout(datetime.timedelta(minutes=3))

    async def warn_user(self, message: discord.Message):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "User": message.author.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id}, 
                {"Guild": message.guild.id, "User": message.author.id, "Score": 1}, 
                upsert=True
            )
            try:
                await self.run_warn(1, message)
                return
            except:
                return
        else:
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id}, 
                {"Guild": message.guild.id, "User": message.author.id, "Score": dbfind["Score"] + 1}, 
                upsert=True
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": message.guild.id, "User": message.author.id}, 
                    {"Guild": message.guild.id, "User": message.author.id, "Score": 0}, 
                    upsert=True
                )
                return await self.run_warn(10, message)
            else:
                try:
                    await self.run_warn(nowscore, message)
                    return
                except:
                    return
                
    async def warn_user_int(self, message: discord.Message, int_: discord.MessageInteractionMetadata):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "User": int_.user.id}, {"_id": False})
        except:
            return print(f"{sys.exc_info()}")
        if dbfind is None:
            await db.replace_one(
                {"Guild": message.guild.id, "User": int_.user.id}, 
                {"Guild": message.guild.id, "User": int_.user.id, "Score": 1}, 
                upsert=True
            )
            try:
                await self.run_warn_int_author(1, message, int_)
                return
            except Exception as e:
                return
        else:
            await db.replace_one(
                {"Guild": message.guild.id, "User": int_.user.id}, 
                {"Guild": message.guild.id, "User": int_.user.id, "Score": dbfind["Score"] + 1}, 
                upsert=True
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": message.guild.id, "User": int_.user.id}, 
                    {"Guild": message.guild.id, "User": int_.user.id, "Score": 0}, 
                    upsert=True
                )
                return await self.run_warn_int_author(10, message, int_)
            else:
                try:
                    await self.run_warn_int_author(nowscore, message, int_)
                    return
                except Exception as e:
                    return

    async def score_get(self, guild: discord.Guild, user: discord.User):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        else:
            return dbfind["Score"]

    @commands.Cog.listener("on_message")
    async def on_message_everyone_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        if "@everyone" in message.content or "@here" in message.content:
            db = self.bot.async_db["Main"].EveryoneBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return

    @commands.Cog.listener("on_message")
    async def on_message_invite_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        INVITE_LINK_REGEX = r"(discord\.(gg|com/invite|app\.com/invite)[/\\][\w-]+)"
        if re.search(INVITE_LINK_REGEX, message.content):
            db = self.bot.async_db["Main"].InviteBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
            if channel_db_find is None:
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
                
    @commands.Cog.listener("on_message")
    async def on_message_token_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        TOKEN_REGEX = r"[A-Za-z\d]{24}\.[\w-]{6}\.[\w-]{27}"
        if re.search(TOKEN_REGEX, message.content):
            db = self.bot.async_db["Main"].TokenBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return

    async def unblock_ch_check(self, message: discord.Message):
        channel_db = self.bot.async_db["Main"].UnBlockChannel
        try:
            channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return False
        if channel_db_find is None:
            return False
        return True

    @commands.Cog.listener("on_message")
    async def on_message_spam_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        try:
            db = self.bot.async_db["Main"].SpamBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            check_ = await self.unblock_ch_check(message)
            if check_:
                return
            message_counts[message.author.id] += 1

            # 指定した回数を超えたら警告
            if message_counts[message.author.id] >= spam_threshold:
                try:
                    await self.warn_user(message)
                except:
                    return
                print(f"SpamDetected: {message.author.id}/{message.author.display_name}")
                message_counts[message.author.id] = 0  # リセット

            # 指定時間後にカウントを減らす
            await asyncio.sleep(time_window)
            message_counts[message.author.id] -= 1
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_userapplication_spam_block(self, message: discord.Message):
        if type(message.channel) == discord.DMChannel:
            return
        if message.interaction_metadata is None:
            return
        try:
            if message.guild.get_member(message.interaction_metadata.user.id).guild_permissions.administrator:
                return
            db = self.bot.async_db["Main"].UserApplicationSpamBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return

            check_ = await self.unblock_ch_check(message)
            if check_:
                return

            message_counts_userapp[message.interaction_metadata.user.id] += 1

            if message_counts_userapp[message.interaction_metadata.user.id] >= 3:
                try:
                    await self.warn_user_int(message, message.interaction_metadata)
                except:
                    return
                print(f"AppSpamDetected: {message.interaction_metadata.user.id}/{message.interaction_metadata.user.display_name}")
                message_counts_userapp[message.interaction_metadata.user.id] = 0

            await asyncio.sleep(time_window)
            message_counts_userapp[message.interaction_metadata.user.id] -= 1
        except:
            return

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel):
            db = self.bot.async_db["Main"].AutoProtectSetting
            try:
                gu = self.bot.get_guild(channel.guild.id).id
                try:
                    dbfind = await db.find_one({"Guild": gu}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_auto_protect_time.get(channel.guild.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_auto_protect_time[channel.guild.id] = current_time
                overwrite = channel.overwrites_for(channel.guild.default_role)
                overwrite.use_external_apps = False
                await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            except:
                return
        elif isinstance(channel, discord.VoiceChannel):
            db = self.bot.async_db["Main"].AutoProtectSetting
            try:
                gu = self.bot.get_guild(channel.guild.id).id
                try:
                    dbfind = await db.find_one({"Guild": gu}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_auto_protect_time.get(channel.guild.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_auto_protect_time[channel.guild.id] = current_time
                overwrite = channel.overwrites_for(channel.guild.default_role)
                overwrite.use_external_apps = False
                await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            except:
                return

    async def check_run_ok_ass(self, message: discord.Message):
        db = self.bot.async_db["Main"].AIChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return True
        if dbfind is None:
            return True
        return False

    async def get_call_pets_random(self, message: discord.Message):
        db = self.bot.async_db["Main"].CallBeasts
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return self.bot.user
        if dbfind is None:
            return self.bot.user
        p = dbfind.get("pet", None)
        if not p:
            return self.bot.user
        return self.bot.get_user(random.choice(p)) if self.bot.get_user(random.choice(p)) else self.bot.user

    async def make_message(self, message: discord.Message):
        if message.content == "":
            return random.choice(["?", "???"])

        if "こんにちは" in message.content:
            return random.choice(["こんちは～", "こんにちは！", "よろしくね！"])

        if "おはよう" in message.content:
            return random.choice(["おはよ～", "おはよ！"])
        
        if "こんばんは" in message.content:
            return random.choice(["こんばんは～", "こんばんは"])
        
        if "（）" in message.content:
            return random.choice(["（）", "（）（）"])
        
        if "()" in message.content:
            return random.choice(["（）", "（）（）"])

        target_categories = ["食べ物", "乗り物", "動物", "果物", "家電", "遊び", "道具", "食材", "携帯電話", "筆記用具", "ソフトウェア", "スポーツ", "偏見", "痛み"]

        def extract_words(text):
            parsed = self.tagger.parse(text)
            lines = parsed.splitlines()
            words = [line.split('\t')[0] for line in lines if '\t' in line]
            return words

        async def fetch_isas(session: ClientSession, word: str):
            url = f"https://api.conceptnet.io/query?start=/c/ja/{word}&rel=/r/IsA&limit=5"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return word, [edge["end"]["label"] for edge in data.get("edges", [])]
            except Exception:
                pass
            return word, []

        async def categorize_words(text):
            words = extract_words(text)
            categories = defaultdict(list)
            categories["その他"] = []

            async with aiohttp.ClientSession() as session:
                tasks = []
                for i, word in enumerate(words):
                    tasks.append(asyncio.create_task(fetch_isas(session, word)))
                    await asyncio.sleep(0.2)

                results = await asyncio.gather(*tasks)

                for word, isas in results:
                    matched = False
                    for category in target_categories:
                        if category in isas:
                            categories[category].append(word)
                            matched = True
                            break
                    if not matched:
                        categories["その他"].append(word)
            
            return categories

        grouped = await categorize_words(message.content)

        food = ["食べたいな", "おいしそう"]
        car = ["、いいね", "乗ってみたいな"]
        pet = ["かわいいね", "いいね！", "かわいい！"]
        kudamono = ["おいしそうだね！"]
        kaden = ["便利そうだね！", "使ってみたいな", "どうやって使うの？"]
        fun = ["楽しそうだね！", "どうやって遊ぶの？", "いいね"]
        tool = ["便利そうだね！", "どうやって使うの？", "使ってみたいな"]
        phone = ["どうやって使うの？", "便利そう！", "写真とりたいな"]
        hikki = ["、それで勉強するよ", "、それで仕事をするよ！", "それで手紙を書いてあげるよ！"]
        supt = ["、楽しそうだね", "、やってみたいな", "のルールを教えてよ"]
        henken = ["じゃないよ", "、なんでそう思うの？", "、それって偏見じゃない？"]
        itami = ["、大丈夫？", "、大丈夫だよ。"]

        texts = []

        for category, words in grouped.items():
            if not words:
                continue
            word_str = "、".join(words)
            if category == "食べ物":
                texts.append(f"{word_str.replace("@", "")} {random.choice(food)}")
            elif category == "乗り物":
                texts.append(f"{word_str.replace("@", "")} {random.choice(car)}")
            elif category == "動物":
                texts.append(f"{word_str.replace("@", "")} {random.choice(pet)}")
            elif category == "果物":
                texts.append(f"{word_str.replace("@", "")} {random.choice(kudamono)}")
            elif category == "家電":
                texts.append(f"{word_str.replace("@", "")} {random.choice(kaden)}")
            elif category == "遊び":
                texts.append(f"{word_str.replace("@", "")} {random.choice(fun)}")
            elif category == "道具":
                texts.append(f"{word_str.replace("@", "")} {random.choice(tool)}")
            elif category == "食材":
                texts.append(f"{word_str.replace("@", "")} {random.choice(food)}")
            elif category == "携帯電話":
                texts.append(f"{word_str.replace("@", "")} {random.choice(phone)}")
            elif category == "筆記用具":
                texts.append(f"{word_str.replace("@", "")} {random.choice(hikki)}")
            elif category == "ソフトウェア":
                texts.append(f"{word_str.replace("@", "")} {random.choice(tool)}")
            elif category == "スポーツ":
                texts.append(f"{word_str.replace("@", "")} {random.choice(supt)}")
            elif category == "偏見":
                texts.append(f"{word_str.replace("@", "")} {random.choice(henken)}")
            elif category == "痛み":
                texts.append(f"{word_str.replace("@", "")} {random.choice(itami)}")

        if not texts:
            return random.choice(["いいね", "なるほど", "！？", "うん"])
        return random.choice(texts)

    @commands.Cog.listener("on_message")
    async def on_message_call_pet(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].CallBeastsChannel
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_pets.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_pets[message.guild.id] = current_time
        pet = await self.get_call_pets_random(message)
        if not pet:
            return await message.reply(embed=discord.Embed(title="まだ召喚獣がいないようです・・", color=discord.Color.yellow(), description="/shopで召喚獣を買えますよ！\nしかも10コインと激安！"))
        await message.add_reaction("🔄")
        try:
            async with aiohttp.ClientSession() as session:
                ch_webhooks = await message.channel.webhooks()
                whname = f"SharkBot-Pets"
                webhooks = discord.utils.get(ch_webhooks, name=whname)
                if webhooks is None:
                    webhooks = await message.channel.create_webhook(name=f"{whname}")
                webhook = Webhook.from_url(webhooks.url, session=session)
                msg = await self.make_message(message)
                await webhook.send(content=msg, username=pet.display_name, avatar_url=pet.avatar.url if pet.avatar else pet.default_avatar.url)
        except:
            try:
                msg = await self.make_message(message)
                await message.reply(embed=discord.Embed(title=pet.display_name, description=msg, color=discord.Color.blue()).set_thumbnail(url=pet.avatar.url if pet.avatar else pet.default_avatar.url))
            except:
                return
            return

    @commands.Cog.listener("on_message")
    async def on_message_shark_assistant(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].SharkAssistant
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        check_as = await self.check_run_ok_ass(message)
        if not check_as:
            return
        current_time = time.time()
        last_message_time = cooldown_sharkass.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_EXPAND:
            return
        cooldown_sharkass[message.guild.id] = current_time
        if not message.mentions == []:
            return
        try:
            if message.content.endswith("を調べて"):
                search_word = message.content.split("を調べて")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("ってなに？"):
                search_word = message.content.split("ってなに？")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("とは"):
                search_word = message.content.split("とは")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("とは？"):
                search_word = message.content.split("とは？")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("ってなんだ？"):
                search_word = message.content.split("ってなんだ？")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("を教えて"):
                search_word = message.content.split("を教えて")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("を検索して"):
                search_word = message.content.split("を検索して")[0]
                await self.search_message(search_word, message)
            elif message.content.endswith("を検索して"):
                search_word = message.content.split("を検索して")[0]
                await self.search_message(search_word, message)
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_expand(self, message: discord.Message):
        if message.author.bot:
            return  # ボットのメッセージは無視
        if not message.content:
            return  # ボットのメッセージは無視
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].ExpandSettings
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_expand_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_EXPAND:
            return
        cooldown_expand_time[message.guild.id] = current_time
        urls = URL_REGEX.findall(message.content)
        if not urls:
            return
        
        await message.add_reaction("🔄")
        
        def randomname(n):
            randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
            return ''.join(randlst)
        for guild_id, channel_id, message_id in urls:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel = await guild.fetch_channel(int(channel_id))
            if not channel:
                continue

            if not type(channel) == discord.Thread:

                if channel.nsfw:
                    if message.channel.nsfw:
                        msg = await channel.fetch_message(int(message_id))
                        embed = discord.Embed(
                            description=msg.content[:1500] if msg.content else "[メッセージなし]",
                            color=discord.Color.green(),
                            timestamp=msg.created_at
                        )
                        embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url, url=f"https://discord.com/users/{msg.author.id}")
                        embed.add_field(name="元のメッセージ", value=f"[リンクを開く]({msg.jump_url})", inline=False)
                        embed.set_footer(text=f"{msg.guild.name} | {msg.channel.name}", icon_url=msg.guild.icon if msg.guild.icon else None)

                        await message.channel.send(embed=embed)

                        return await message.add_reaction("✅")
                    else:
                        return await message.add_reaction("❌")

            try:
                msg = await channel.fetch_message(int(message_id))
                embed = discord.Embed(
                    description=msg.content[:1500] if msg.content else "[メッセージなし]",
                    color=discord.Color.green(),
                    timestamp=msg.created_at
                )
                embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url, url=f"https://discord.com/users/{msg.author.id}")
                embed.add_field(name="元のメッセージ", value=f"[リンクを開く]({msg.jump_url})", inline=False)
                embed.set_footer(text=f"{msg.guild.name} | {msg.channel.name}", icon_url=msg.guild.icon if msg.guild.icon else None)

                await message.channel.send(embed=embed)

                return await message.add_reaction("✅")
            except Exception as e:
                return await message.add_reaction("❌")

    @commands.Cog.listener("on_member_update")
    async def on_member_update_timeout_removerole(self, before: discord.Member, after: discord.Member):
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is not None:  # タイムアウトされた
                db = self.bot.async_db["Main"].AutoRoleRemover
                try:
                    g = self.bot.get_guild(after.guild.id)
                    dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                role = after.guild.get_role(dbfind["Role"])
                if role in after.roles:
                    try:
                        await after.remove_roles(role)
                    except discord.Forbidden:
                        return
                    except discord.HTTPException as e:
                        return

    @commands.hybrid_group(name="api-setting", description="いろいろなAPIの設定をします。", fallback="x")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def api_setting_x(self, ctx: commands.Context):
        class send(discord.ui.Modal):
            def __init__(self, database) -> None:
                super().__init__(title="XAPIの設定", timeout=None)
                self.db = database
                self.key = discord.ui.TextInput(label="API Key",placeholder="APIKeyを入れる",style=discord.TextStyle.short,required=True)
                self.sec = discord.ui.TextInput(label="API SECRET",placeholder="APISECRETを入れる",style=discord.TextStyle.short,required=True)
                self.act = discord.ui.TextInput(label="Access Token",placeholder="AccessTokenを入れる",style=discord.TextStyle.short,required=True)
                self.acts = discord.ui.TextInput(label="Access Token Secret",placeholder="AccessTokenSecretを入れる",style=discord.TextStyle.short,required=True)
                self.beatoken = discord.ui.TextInput(label="Bearer Token",placeholder="Bearer Tokenを入れる",style=discord.TextStyle.short,required=True)
                self.add_item(self.key)
                self.add_item(self.sec)
                self.add_item(self.act)
                self.add_item(self.acts)
                self.add_item(self.beatoken)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                db = self.db["Main"].XAPISetting
                await db.replace_one(
                    {"User": ctx.author.id}, 
                    {"User": ctx.author.id, "APIKey": self.key.value, "APISECRET": self.sec.value, "APITOKEN": self.act.value, "APITOKENSECRET": self.acts.value, "BearerToken": self.beatoken.value}, 
                    upsert=True
                )
                await interaction.response.send_message(embed=discord.Embed(title="XAPIの設定をしました。", color=discord.Color.green()), ephemeral=True)
        await ctx.interaction.response.send_modal(send(self.bot.async_db))

    def randomname(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    @api_setting_x.command(name="sharkbot", description="SharkBotのWebAPIKeyを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def api_setting_sharkbot(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        tk = self.randomname(40)
        db = self.bot.async_db["Main"].AuthToken
        await db.replace_one(
            {"Guild": ctx.guild.id},
            {"Token": tk, "Guild": ctx.guild.id, "GuildName": ctx.guild.name, "Author": ctx.author.id, "AuthorName": ctx.author.name},
            upsert=True
        )
        await ctx.reply(f"発行されたWebAPIKey: `{tk}`", ephemeral=True)

    @commands.hybrid_group(name="settings", description="ようこそメッセージを設定します。", fallback="welcome")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def welcome_setting(self, ctx: commands.Context, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="ようこそメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].WelcomeMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Description": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="ウェルカムメッセージを有効化しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].WelcomeMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            await ctx.reply(embed=discord.Embed(title="ウェルカムメッセージを無効化しました。", color=discord.Color.green()))

    @welcome_setting.command(name="goodbye", description="さようならメッセージを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def goodbye_message(self, ctx, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="さようならメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].GoodByeMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Description": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="さようならメッセージを有効化しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].GoodByeMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            await ctx.reply(embed=discord.Embed(title="さようならメッセージを無効化しました。", color=discord.Color.green()))

    @welcome_setting.command(name="stickrole", description="ロールをくっつけます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def stick_role(self, ctx, ユーザー: discord.User, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].StickRole
        if ロール:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ユーザー.id}, 
                {"Guild": ctx.guild.id, "User": ユーザー.id, "Role": ロール.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ユーザーにロールをくっつけました。", description=f"ユーザー: `{ロール.name}`\nロール: `{ロール.name}`", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "User": ユーザー.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="その人にロールはくっついていません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ロールを剝がしました。", color=discord.Color.red()))

    @welcome_setting.command(name="lock-message", description="メッセージを固定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def lock_message(self, ctx: commands.Context, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="メッセージ固定の設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    msg = await interaction.channel.send(embed=discord.Embed(title=self.etitle.value, description=self.desc.value, color=discord.Color.random()), view=LockMessageRemove())
                    db = self.db["Main"].LockMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Desc": self.desc.value, "MessageID": msg.id}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="メッセージ固定を有効化しました。", color=discord.Color.green()), ephemeral=True)
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].LockMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="メッセージ固定は有効化されていません。", color=discord.Color.red()))    
            await ctx.reply(embed=discord.Embed(title="メッセージ固定を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="register", description="サーバー掲示板にサーバーを掲載します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def register_server(self, ctx: commands.Context, 説明: str):
        if ctx.guild.icon == None:
            return await ctx.reply("サーバー掲示板に乗せるにはアイコンを設定する必要があります。")
        db = self.bot.async_db["Main"].Register
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Name": ctx.guild.name, "Description": 説明, "Invite": inv.url, "Icon": ctx.guild.icon.url}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="サーバーを掲載しました。", color=discord.Color.green()))

    @welcome_setting.command(name="management", description="運営を募集します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def management_server(self, ctx: commands.Context, 仕事内容: str):
        await ctx.defer()
        if ctx.guild.icon == None:
            return await ctx.reply("運営募集掲示板に乗せるにはアイコンを設定する必要があります。")
        db = self.bot.async_db["Main"].ManagementRegister
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Name": ctx.guild.name, "Description": 仕事内容, "Invite": inv.url, "Icon": ctx.guild.icon.url}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="サーバーを運営募集掲示板に掲載しました。", color=discord.Color.green()))

    @welcome_setting.command(name="emoji-translate", description="絵文字をつけると翻訳します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def emoji_translate(self, ctx: commands.Context, 有効にするか: bool):
        db = self.bot.async_db["Main"].EmojiTranslate
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="絵文字翻訳を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="絵文字翻訳は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="絵文字翻訳を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="prefix", description="Prefixを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_prefix(self, ctx: commands.Context, prefix: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].CustomPrefixBot
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Prefix": prefix}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Prefixを設定しました。", description=f"「{prefix}」", color=discord.Color.green()))

    @welcome_setting.command(name="score", description="スコアをチェックします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_score(self, ctx: commands.Context, ユーザー: discord.User):
        class ScoreSettingView(discord.ui.View):
            def __init__(self, db, ユーザーs):
                super().__init__(timeout=None)
                self.db = db
                self.ユーザー = ユーザーs

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="スコアに関しての設定",
                options=[
                    discord.SelectOption(label="スコアを9に設定"),
                    discord.SelectOption(label="スコアを8に設定"),
                    discord.SelectOption(label="スコアを5に設定"),
                    discord.SelectOption(label="スコアを3に設定"),
                    discord.SelectOption(label="スコアをクリア"),
                ]
            )
            async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id == ctx.author.id:
                    if "スコアを8に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 8}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id.id, "Score": 8}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを8に設定しました。", ephemeral=True)
                    elif "スコアを5に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 5}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 5}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを5に設定しました。", ephemeral=True)
                    elif "スコアを3に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 3}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 3}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを3に設定しました。", ephemeral=True)
                    elif "スコアを9に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 9}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 9}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを9に設定しました。", ephemeral=True)
                    elif "スコアをクリア" == select.values[0]:
                        db = self.db.WarnUserScore
                        result = await db.delete_one({"Guild": interaction.guild.id, "User": self.ユーザー.id})
                        await interaction.response.send_message("スコアをクリアしました。", ephemeral=True)
        sc = await self.score_get(ctx.guild, ユーザー)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}さんのスコア", description=f"スコア: {sc}", color=discord.Color.green()), view=ScoreSettingView(self.bot.async_db["Main"], ユーザー))

    @welcome_setting.command(name="warn-setting", description="警告時に実行するものを選択します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_warn_setting(self, ctx: commands.Context, スコア: int = None):
        class ScoreView(discord.ui.View):
            def __init__(self, スコア: int, db):
                super().__init__(timeout=None)
                self.db = db
                self.sc = スコア

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="警告時の設定",
                options=[
                    discord.SelectOption(label="タイムアウト3分"),
                    discord.SelectOption(label="タイムアウト5分"),
                    discord.SelectOption(label="タイムアウト10分"),
                    discord.SelectOption(label="Kick"),
                    discord.SelectOption(label="BAN"),
                    discord.SelectOption(label="なし"),
                ]
            )
            async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id == ctx.author.id:
                    if "タイムアウト3分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 0}, 
                            upsert=True
                        )
                    elif "タイムアウト5分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 1}, 
                            upsert=True
                        )
                    elif "タイムアウト10分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 2}, 
                            upsert=True
                        )
                    elif "Kick" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 3}, 
                            upsert=True
                        )
                    elif "BAN" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 4}, 
                            upsert=True
                        )
                    elif "なし" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Score": self.sc}, 
                            {"Guild": ctx.guild.id, "Score": self.sc, "Setting": 5}, 
                            upsert=True
                        )
                    await interaction.response.send_message(f"設定しました。\n{self.sc}: {select.values[0]}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"あなたはコマンドの実行者ではありません。", ephemeral=True)
        s1 = await self.get_score_warn(ctx.guild, 1)
        s2 = await self.get_score_warn(ctx.guild, 2)
        s3 = await self.get_score_warn(ctx.guild, 3)
        s4 = await self.get_score_warn(ctx.guild, 4)
        s5 = await self.get_score_warn(ctx.guild, 5)
        s6 = await self.get_score_warn(ctx.guild, 6)
        s7 = await self.get_score_warn(ctx.guild, 7)
        s8 = await self.get_score_warn(ctx.guild, 8)
        s9 = await self.get_score_warn(ctx.guild, 9)
        s10 = await self.get_score_warn(ctx.guild, 10)

        if スコア:

            await ctx.reply(view=ScoreView(スコア, self.bot.async_db["Main"]), embed=discord.Embed(title="警告時の設定", description=f"""
1. {self.return_warn_text(s1)}
2. {self.return_warn_text(s2)}
3. {self.return_warn_text(s3)}
4. {self.return_warn_text(s4)}
5. {self.return_warn_text(s5)}
6. {self.return_warn_text(s6)}
7. {self.return_warn_text(s7)}
8. {self.return_warn_text(s8)}
9. {self.return_warn_text(s9)}
10. {self.return_warn_text(s10)}
            """, color=discord.Color.blue()))
        else:
            await ctx.reply(embed=discord.Embed(title="警告時の設定リスト", description=f"""
1. {self.return_warn_text(s1)}
2. {self.return_warn_text(s2)}
3. {self.return_warn_text(s3)}
4. {self.return_warn_text(s4)}
5. {self.return_warn_text(s5)}
6. {self.return_warn_text(s6)}
7. {self.return_warn_text(s7)}
8. {self.return_warn_text(s8)}
9. {self.return_warn_text(s9)}
10. {self.return_warn_text(s10)}
            """, color=discord.Color.blue()))

    @welcome_setting.command(name="automod", description="AutoModを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_automod(self, ctx: commands.Context):
        class AutoModView(discord.ui.View):
            def __init__(self, db):
                super().__init__(timeout=None)
                self.db = db

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="設定するAutoModを選択",
                options=[
                    discord.SelectOption(label="招待リンク"),
                    discord.SelectOption(label="Token"),
                    discord.SelectOption(label="スパム"),
                    discord.SelectOption(label="EvryoneとHere"),
                    discord.SelectOption(label="メールアドレス"),
                    discord.SelectOption(label="GIF対策"),
                    discord.SelectOption(label="長いURL対策"),
                    discord.SelectOption(label="スラッシュコマンド荒らし"),
                    discord.SelectOption(label="ブロックしないチャンネルの設定"),
                    discord.SelectOption(label="ブロックしないチャンネルの解除"),
                    discord.SelectOption(label="無効化"),
                ]
            )
            async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id == ctx.author.id:
                    if "招待リンク" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="招待リンク対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"(discord\.(gg|com/invite|app\.com/invite)[/\\][\w-]+)"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "Token" == select.values[0]:
                        dbs = self.db.TokenBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "スパム" == select.values[0]:
                        dbs = self.db.SpamBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "EvryoneとHere" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="Everyone対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"@everyone", r"@here"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "メールアドレス" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="メールアドレス対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"^[a-zA-Z0-9_+-]+(.[a-zA-Z0-9_+-]+)*@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}$"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "GIF対策" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="GIF対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"https?://tenor.com/.*", r"https?://cdn.discordapp.com/attachments/.*.gif", r"https?://.*.gif"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "GIF対策" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="GIF対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"https?://tenor.com/.*", r"https?://cdn.discordapp.com/attachments/.*.gif", r"https?://.*.gif"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "長いURL対策" == select.values[0]:
                        await interaction.guild.create_automod_rule(
                            name="長いURL対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=[r"https:\/\/o{10,}\.ooo\/.*"]),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    elif "スラッシュコマンド荒らし" == select.values[0]:
                        dbs = self.db.UserApplicationSpamBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "ブロックしないチャンネルの設定" == select.values[0]:
                        dbs = self.db.UnBlockChannel
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                            upsert=True
                        )
                        return await interaction.response.send_message(f"ブロックしないチャンネルの設定をしました。\n{interaction.channel.mention}", ephemeral=True)
                    elif "ブロックしないチャンネルの解除" == select.values[0]:
                        dbs = self.db.UnBlockChannel
                        await dbs.delete_one({"Channel": ctx.channel.id})
                        return await interaction.response.send_message(f"ブロックしないチャンネルの解除をしました。\n{interaction.channel.mention}", ephemeral=True)
                    elif "無効化" == select.values[0]:
                        await interaction.response.defer(ephemeral=True)
                        dbs = self.db.InviteBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.TokenBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.SpamBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.EveryoneBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.UserApplicationSpamBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        rule = await ctx.guild.fetch_automod_rules()
                        for r in rule:
                            if r.name == "Everyone対策":
                                await r.delete()
                                await asyncio.sleep(1)
                            elif r.name == "招待リンク対策":
                                await r.delete()
                                await asyncio.sleep(1)
                            elif r.name == "メールアドレス対策":
                                await r.delete()
                                await asyncio.sleep(1)
                            elif r.name == "GIF対策":
                                await r.delete()
                                await asyncio.sleep(1)
                            elif r.name == "長いURL対策":
                                await r.delete()
                                await asyncio.sleep(1)
                        return await interaction.followup.send(f"無効化しました。", ephemeral=True)
                    await interaction.response.send_message(f"AutoModを有効にしました。\n{select.values[0]}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"あなたはコマンドの実行者ではありません。", ephemeral=True)
        await ctx.reply(view=AutoModView(self.bot.async_db["Main"]), embed=discord.Embed(title="AutoModの設定", color=discord.Color.blue()))

    @welcome_setting.command(name="expand", description="メッセージ展開を有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_message_expand(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].ExpandSettings
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="メッセージ展開を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="メッセージ展開は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="メッセージ展開を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="expand-user", description="ユーザー展開を有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_user_expand(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].ExpandSettingsUser
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ユーザー展開を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ユーザー展開は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ユーザー展開を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="timeout-roleremove", description="タイムアウトされるとロールを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_timeout_roleremove(self, ctx: commands.Context, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].AutoRoleRemover
        if ロール:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Role": ロール.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ロール自動削除を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ロール自動削除は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ロール自動削除を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="english-only", description="英語専用チャンネルを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_eng_only(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].EnglishOnlyChannel
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="英語専用チャンネルを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="英語専用チャンネルは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="英語専用チャンネルを無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="hint", description="ヒントを有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_hint(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].HintSetting
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ヒントを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ヒントは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ヒントを無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="auto-protect", description="自動的に、チャンネルの権限を奪います。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_autoprotect(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].AutoProtectSetting
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="自動チャンネル保護機能を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="自動チャンネル保護機能は有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="自動チャンネル保護機能を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="shark-assistant", description="discord上でアシスタント機能を使います。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_assistant(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].SharkAssistant
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="Sharkアシスタントを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="Sharkアシスタントは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="Sharkアシスタントを無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="call-pet", description="召喚獣と遊べるチャンネルを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_call_pet(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].CallBeastsChannel
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="召喚獣と遊ぶチャンネルを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="召喚獣と遊ぶチャンネルは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="召喚獣と遊ぶチャンネルを無効化しました。", color=discord.Color.red()))

    async def announce_pun_set_setting(self, guild: discord.Guild, channel: discord.TextChannel, tf = False):
        db = self.bot.async_db["Main"].AnnouncePun
        if not tf:
            return await db.delete_one({"Guild": guild.id})
        else:
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id}, 
                {"Guild": guild.id, "Channel": channel.id}, 
                upsert=True
            )

    @welcome_setting.command(name="auto-publish", description="自動アナウンス公開をします。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def auto_publication(self, ctx: commands.Context, チャンネル: discord.TextChannel, 有効にするか: bool):
        try:
            await ctx.defer()
            await self.announce_pun_set_setting(ctx.guild, チャンネル, 有効にするか)
            await ctx.reply(embed=discord.Embed(title="自動アナウンス公開を設定しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="自動アナウンス公開を設定できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @welcome_setting.command(name="file-deletor", description="自動的に削除するファイル形式を設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    @app_commands.choices(操作=[
        app_commands.Choice(name='追加',value="add"),
        app_commands.Choice(name='削除',value="remove"),
    ])
    async def file_deletor(self, ctx: commands.Context, 操作: app_commands.Choice[str], 拡張子: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].FileAutoDeletor
        if 操作.value == "add":
            await db.update_one(
                {"guild_id": ctx.guild.id},
                {"$addToSet": {"end": 拡張子.replace(".", "")}},
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"`.{拡張子.replace(".", "")}`をブロックするようにしました。", color=discord.Color.green()))
        else:
            await db.update_one(
                {"guild_id": ctx.guild.id},
                {"$pull": {"end": 拡張子.replace(".", "")}}
            )
            await ctx.reply(embed=discord.Embed(title=f"`.{拡張子.replace(".", "")}`をブロックしないようにしました。", color=discord.Color.green()))

    @welcome_setting.command(name="auto-translate", description="自動翻訳をします。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(翻訳先=[
        app_commands.Choice(name='日本語へ',value="ja"),
        app_commands.Choice(name='英語へ',value="en"),
    ])
    async def auto_translate(self, ctx: commands.Context, 翻訳先: app_commands.Choice[str], 有効にするか: bool):
        db = self.bot.async_db["Main"].AutoTranslate
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Lang": 翻訳先.value}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="自動翻訳を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="自動翻訳は有効化されていません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="自動翻訳を無効化しました。", color=discord.Color.red()))

"""
    @commands.command(name="voice_date", description="最後にVCを使用した日付を貼り付けます。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def voice_date(self, ctx, voice: discord.VoiceChannel = None):
        try:
            db = self.bot.async_db["Main"].VoiceTime
            if voice:
                await db.replace_one(
                    {"Channel": voice.id}, 
                    {"Channel": voice.id, "Guild": ctx.guild.id}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="最後にVCに参加した日付を記録するようにしました。", color=discord.Color.green()))
            else:
                await db.delete_one({"Guild": ctx.guild.id})
                await ctx.reply(embed=discord.Embed(title="最後にVCに参加した日付を記録しないようにしました。", color=discord.Color.green()))
        except:
            return
"""
async def setup(bot):
    await bot.add_cog(SettingCog(bot))