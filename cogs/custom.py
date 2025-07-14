from discord.ext import commands
import discord
import io
import traceback
from functools import partial
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
import sys
from discord import app_commands
import json
import requests
import logging
import urllib
import random
import re
import datetime
import aiohttp
import time
import asyncio
from PIL import ImageFont, Image, ImageDraw

COOLDOWN_TIME = 10
user_last_message_time = {}

NG_WORDS = [
    # 一般的な下ネタ（日本語）
    "ちんこ", "まんこ", "おっぱい", "アナル", "フェラ", "セックス", "レイプ", "精子", "膣", "陰茎",
    "陰部", "射精", "勃起", "変態", "エロ", "裸", "スカトロ", "童貞", "処女", "肉便器", "中出し", "ハメ撮り",
    
    # 一般的な下ネタ（英語）
    "fuck", "shit", "bitch", "cock", "dick", "pussy", "ass", "boobs", "tits",
    "anal", "blowjob", "cum", "semen", "vagina", "penis", "rape", "orgasm", "masturbation",
    
    # その他、問題になりそうな言葉（ネットスラングなど）
    "きんたま", "ズリネタ", "オナニー", "セフレ", "孕む", "潮吹き", "クリトリス",
    "ガチホモ", "ホモ", "ゲイポルノ", "ロリコン", "ペド", "ペドフィリア", "近親相姦"
]

class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.pages = self.generate_pages()
        self.current_page = 0
        self.set_page_footer()

    def generate_pages(self):
        visible_commands = [cmd for cmd in self.bot.commands if not cmd.hidden]

        categories = {}
        for command in visible_commands:
            if isinstance(command, commands.HybridGroup):
                # グループコマンド（サブコマンドを含む）
                subcommands = [
                    f"`/{command.name} {sub.name}`: {sub.description or '説明なし'}"
                    for sub in command.commands if not sub.hidden
                ]
                if command.invoke_without_command:
                    subcommands.insert(0, f"`/{command.name} {command.fallback}`: {command.description or '説明なし'}")
                categories[command.name] = subcommands
            elif isinstance(command, commands.HybridCommand):
                # 一般コマンド
                cog_name = "一般"
                if cog_name not in categories:
                    categories[cog_name] = []
                categories[cog_name].append(f"`/{command.name}`: {command.description or '説明なし'}")

        field_count = 0
        pages = []
        current_embed = None
        for category, commands_list in categories.items():
            if current_embed is None:
                current_embed = discord.Embed(
                    title=f"ヘルプ",
                    description="以下は利用可能なコマンド一覧です。",
                    color=discord.Color.blue()
                )

            for command in commands_list:
                if field_count >= 10:  # フィールド数が20を超えたら新しいEmbedを作成
                    pages.append(current_embed)
                    current_embed = discord.Embed(
                        title=f"ヘルプ",
                        description="以下は利用可能なコマンド一覧です。",
                        color=discord.Color.blue()
                    )
                    field_count = 0

                current_embed.add_field(name=command.split(":")[0], value=command.split(":")[1], inline=False)
                field_count += 1

        if not pages:
            pages.append(discord.Embed(
                title="ヘルプ",
                description="現在利用可能なコマンドはありません。",
                color=discord.Color.red()
            ))
        return pages

    def set_page_footer(self):
        total_pages = len(self.pages)
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"ページ {self.current_page + 1} / {total_pages}")

    @discord.ui.button(label="戻る", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.set_page_footer()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.set_page_footer()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="閉じる", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="ヘルプメニューを閉じました。", embed=None, view=None)

class CustomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CustomCog")

    class Compile():
        def __init__(self, code: str, bot: commands.Bot):
            self.code = code
            self.logs = ""
            self.message = None
            self.echoad_msg = None
            self.bot = bot
            pass

        def replace_code(self, code: str):
            replaced_code = code.replace("{avatar}", self.message.author.avatar.url if self.message.author.avatar else self.message.author.default_avatar.url)
            replaced_code = replaced_code.replace("{name}", self.message.author.name)
            replaced_code = replaced_code.replace("{id}", str(self.message.author.id))
            replaced_code = replaced_code.replace("{g_id}", str(self.message.guild.id))
            replaced_code = replaced_code.replace("{g_name}", self.message.guild.name)
            replaced_code = replaced_code.replace("{g_memc}", str(self.message.guild.member_count))
            replaced_code = replaced_code.replace("{nowtime}", str(datetime.datetime.now()))
            try:
                replaced_code = replaced_code.replace("{arg1}", self.message.content.split(" ")[1])
            except:
                replaced_code = replaced_code.replace("{arg1}", "None")
                pass
            try:
                replaced_code = replaced_code.replace("{arg2}", self.message.content.split(" ")[2])
            except:
                replaced_code = replaced_code.replace("{arg2}", "None")
                pass
            try:
                replaced_code = replaced_code.replace("{arg3}", self.message.content.split(" ")[3])
            except:
                replaced_code = replaced_code.replace("{arg3}", "None")
                pass
            return replaced_code
        
        def tokenize(self, code: str):
            lines = self.replace_code(code).strip().splitlines()
            instructions = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                if line.startswith("if "):
                    match = re.match(r'if\s+(".*?"|\w+)\s*==\s*(".*?"|\w+)', line)
                    if not match:
                        continue
                    left, right = match.groups()
                    i += 1

                    if_block, else_block = [], []
                    while i < len(lines) and lines[i].startswith("    "):
                        if_block.append(lines[i][4:])
                        i += 1
                    if i < len(lines) and lines[i].strip() == "else":
                        i += 1
                        while i < len(lines) and lines[i].startswith("    "):
                            else_block.append(lines[i][4:])
                            i += 1

                    instructions.append(("IFELSE_EXPR", left, right,
                                        self.tokenize("\n".join(if_block)),
                                        self.tokenize("\n".join(else_block))))
                    continue


                elif line.startswith("print "):
                    match = re.match(r'print\s+(\w+|".*")', line)
                    if match:
                        val = match.group(1)
                        if val.startswith('"') and val.endswith('"'):
                            instructions.append(("PRINT", val[1:-1]))
                        else:
                            instructions.append(("PRINT_VAR", val))
                        i += 1
                        continue
                    else:
                        return

                elif line.startswith("echo "):
                    match = re.match(r'echo\s+(\w+|".*")', line)
                    if match:
                        val = match.group(1)
                        if val.startswith('"') and val.endswith('"'):
                            instructions.append(("ECHO", val[1:-1]))
                        else:
                            instructions.append(("ECHO_VAR", val))
                        i += 1
                        continue
                    else:
                        i += 1
                        continue

                elif line.startswith("reaction "):
                    match = re.match(r'reaction\s+"(.*)"', line)
                    if match:
                        instructions.append(("REACTION", match.group(1)))
                    i += 1
                    continue

                elif line.startswith("echoad_reaction "):
                    match = re.match(r'echoad_reaction\s+"(.*)"', line)
                    if match:
                        instructions.append(("ECHO_REACTION", match.group(1)))
                    i += 1
                    continue

                elif line.startswith("afk "):
                    match = re.match(r'afk\s+"(.*)"', line)
                    if match:
                        instructions.append(("AFKSETTING", match.group(1)))
                    i += 1
                    continue

                elif line.startswith("embed "):
                    match = re.match(r'embed\s+"(.*)"\s+"(.*)"\s+"(.*)"', line)
                    if match:
                        instructions.append(("EMBED", match.group(1), match.group(2), match.group(3)))
                    i += 1
                    continue

                elif "=" in line:
                    var, expr = map(str.strip, line.split("=", 1))

                    # match_http = re.match(r'http_get\s+"(.*)"', expr)
                    # if match_http:
                    #     url_var = match_http.group(1)
                    #     instructions.append(("HTTP_GET", var, url_var))
                    #     i += 1
                    #     continue

                    match_random = re.match(r'random\s+"(.*)"', expr)
                    if match_random:
                        rdnameiyou = match_random.group(1)
                        instructions.append(("RANDOM", var, rdnameiyou))
                        i += 1
                        continue

                    match_str = re.match(r'"(.*)"', expr)
                    if match_str:
                        instructions.append(("SET", var, match_str.group(1)))
                        i += 1
                        continue
                    else:
                        return

                else:
                    i += 1
                    continue

            return instructions

        async def interpret(self, instructions, message: discord.Message):
            variables = {}
            
            def replace_variable(word: str):
                for k, v in variables.items():
                    word = word.replace("{" + k + "}", v)
                return word

            async def eval_instructions(insts):
                nonlocal variables
                for inst in insts:
                    if inst[0] == "SET":
                        variables[inst[1]] = replace_variable(inst[2])

                    elif inst[0] == "RANDOM":
                        variables[inst[1]] =replace_variable(random.choice(inst[2].split("|")))

                    elif inst[0] == "PRINT":
                        self.logs += replace_variable(inst[1]) + "\n"

                    elif inst[0] == "PRINT_VAR":
                        self.logs += variables.get(inst[1], f"[undefined: {inst[1]}]") + "\n"

                    elif inst[0] == "ECHO_VAR":
                        msg = await message.channel.send(
                            f"{variables.get(inst[1], f'[undefined: {inst[1]}]').replace("\\n", "\n")}\n-# これはカスタムコマンドからの発言です。"
                        )
                        self.echoad_msg = msg
                        await asyncio.sleep(1)

                    elif inst[0] == "ECHO":
                        msg = await message.channel.send(
                            f"{replace_variable(inst[1].replace("\\n", "\n"))}\n-# これはカスタムコマンドからの発言です。"
                        )
                        self.echoad_msg = msg
                        await asyncio.sleep(1)

                    elif inst[0] == "EMBED":
                        msg = await message.channel.send(
                            embed=discord.Embed(title=f"{replace_variable(inst[1].replace("\\n", "\n"))}", description=f"{replace_variable(inst[2].replace("\\n", "\n"))}", color=discord.Color.from_rgb(int(inst[3].split(",")[0]), int(inst[3].split(",")[1]), int(inst[3].split(",")[2]))).set_footer(text="これはカスタムコマンドからの発言です。")
                        )
                        self.echoad_msg = msg
                        await asyncio.sleep(1)

                    elif inst[0] == "REACTION":
                        try:
                            await message.add_reaction(inst[1])
                        except:
                            continue
                        await asyncio.sleep(1)

                    elif inst[0] == "ECHO_REACTION":
                        try:
                            await self.echoad_msg.add_reaction(inst[1])
                        except:
                            continue
                        await asyncio.sleep(1)

                    elif inst[0] == "AFKSETTING":
                        try:
                            await self.bot.async_db["Main"].AFK.replace_one(
                                {"User": message.author.id}, 
                                {"User": message.author.id, "Reason": inst[1]}, 
                                upsert=True
                            )
                        except:
                            continue

                    elif inst[0] == "IFELSE_EXPR":
                        left, right = inst[1], inst[2]

                        def resolve(val):
                            if val.startswith('"') and val.endswith('"'):
                                content = val[1:-1]
                            else:
                                content = variables.get(val, "")
                            return re.sub(r"\{(\w+)\}", lambda m: variables.get(m.group(1), ""), content)

                        left_val = resolve(left)
                        right_val = resolve(right)

                        if left_val == right_val:
                            await eval_instructions(inst[3])
                        else:
                            await eval_instructions(inst[4])

            await eval_instructions(instructions)

        async def run(self, message: discord.Message):
            self.message = message
            tokens = self.tokenize(self.code)
            await self.interpret(tokens, message)
            if self.logs == "":
                return None
            return self.logs

    async def get_commands(self, guild: discord.Guild):
        try:
            cp = self.bot.async_db["Main"].CustomCommand_v2
            async with cp.find({"Guild": guild.id}) as cursor:
                commands = await cursor.to_list(length=None)

            return ["?" + command["Name"] for command in commands]
        except:
            return ["登録なし"]
    
    async def get_command(self, guild: discord.Guild, cmdname: str):
        try:
            cp = self.bot.async_db["Main"].CustomCommand_v2
            try:
                dbfind = await cp.find_one({"Guild": guild.id, "Name": cmdname}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            return dbfind["Program"]
        except:
            return None

    @commands.Cog.listener(name="on_message")
    async def on_message_command(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content.startswith("?"):
            return
        current_time = time.time()
        last_message_time = user_last_message_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time[message.guild.id] = current_time
        try:
            cmd_name = message.content.split("?")[1].split(" ")[0]
            prog = await self.get_command(message.guild, cmd_name)
            if not prog:
                return
            output = await self.Compile(prog, self.bot).run(message)
            if not output:
                return
            await message.reply(embed=discord.Embed(title="カスタムコマンドの出力", description=output, color=discord.Color.green()))
        except:
            print(f"{sys.exc_info()}")
            return

    @commands.hybrid_command(name = "help", with_app_command = True, description = "ヘルプを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def help_slash(self, ctx: commands.Context):
        await ctx.defer()
        pages = []

        for c in self.bot.commands:
            if type(c) == commands.HybridCommand:
                pages.append(discord.Embed(title=f"/{c.name}", description=f"{c.description}", color=discord.Color.blue()))
            elif type(c) == commands.HybridGroup:
                embed = discord.Embed(title=f"/{c.name}", color=discord.Color.blue())
                text = ""
                text += f"{c.fallback} .. {c.description}\n"
                for cc in c.commands:
                    text += f"{cc.name} .. {cc.description}\n"
                embed.description = text
                pages.append(embed)

        class Help_view(discord.ui.View):
            def __init__(self, get_commands):
                super().__init__()
                self.get_commands = get_commands
                self.current_page = 0
                self.update_buttons()

            def update_buttons(self):
                self.clear_items()
                self.add_item(discord.ui.Button(emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="help_prev"))
                self.add_item(discord.ui.Button(label=f"{self.current_page + 1}/{len(pages)}", style=discord.ButtonStyle.secondary, disabled=True))
                self.add_item(discord.ui.Button(emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="help_next"))
                self.add_item(discord.ui.Button(label="カスタムコマンド", style=discord.ButtonStyle.red, custom_id="help_custom"))

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.data["custom_id"] == "help_prev":
                    if self.current_page > 0:
                        self.current_page -= 1
                elif interaction.data["custom_id"] == "help_next":
                    if self.current_page < len(pages) - 1:
                        self.current_page += 1
                    else:
                        self.current_page = 0
                elif interaction.data["custom_id"] == "help_custom":
                    cmds = await self.get_commands(interaction.guild)
                    await interaction.response.edit_message(embed=discord.Embed(title="カスタムコマンドヘルプ", description=f"""
{"\n".join(cmds)}
""", color=discord.Color.red()))
                    return
                self.update_buttons()
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)
                return True

        view = Help_view(self.get_commands)
        await ctx.reply(embed=pages[0], view=view)

    """
        if カテゴリ:
            return await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/commands?id={ctx.guild.id}")
        return await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/commands?id={ctx.guild.id}")
        if not カテゴリ:
            view = HelpView(self.bot)
            return await ctx.reply(embed=view.pages[0], view=view)
        if カテゴリ == "commands":
            prefix = await self.get_prefix(ctx.guild)
            cmds = await self.get_commands(ctx.guild)
            await ctx.reply(embed=discord.Embed(title="`commands`プラグイン", description=f"{"\n".join(cmds)}", color=discord.Color.blue()).set_footer(text=f"Prefix: {prefix}"))
        elif カテゴリ == "help":
            await ctx.reply(embed=discord.Embed(title="`help`プラグイン", color=discord.Color.blue()).add_field(name="`help`", value="ヘルプを見ます。"))
        else:
            embed = discord.Embed(title=f"`{カテゴリ}`プラグイン", color=discord.Color.blue())
            for command in self.bot.tree.get_commands():
                if isinstance(command, app_commands.Group):
                    if command.name == f"{カテゴリ}":
                        for subcommand in command.commands:
                            embed.add_field(name=f"`{subcommand.name}`", value=f"{subcommand.description}")
                        break
            return await ctx.reply(embed=embed)
    """

    @commands.hybrid_group(name="custom", description="カスタムコマンドのPrefixを設定します。", fallback="create")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def custom_create(self, ctx):
        try:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="カスタムコマンドの作成", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="コマンド名",placeholder="animal",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="プログラム",placeholder="print shark is bot",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].CustomCommand_v2
                    await db.replace_one(
                        {"Guild": ctx.guild.id, "Name": self.etitle.value}, 
                        {"Guild": ctx.guild.id, "Name": self.etitle.value, "Program": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="カスタムコマンドを作成しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        except:
            return
        
    @custom_create.command(name="remove", description="カスタムコマンドを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def custom_remove(self, ctx, コマンド名: str):
        try:
            db = self.bot.async_db["Main"].CustomCommand_v2
            result = await db.delete_one({
                "Guild": ctx.guild.id, "Name": コマンド名,
            })
            await ctx.reply(embed=discord.Embed(title="カスタムコマンドを削除しました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return

    @custom_create.command(name="export", description="カスタムコマンドのプログラムを書き出します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def custom_export(self, ctx: commands.Context, コマンド名: str):
        prog = await self.get_command(ctx.guild, コマンド名)
        if not prog:
            return await ctx.reply(embed=discord.Embed(title="コマンドが見つかりませんでした。", color=discord.Color.red()))
        i = io.StringIO(prog)
        await ctx.reply(file=discord.File(i, filename="cmd.txt"))
        i.close()

    @commands.command(name="help_beta")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def beta_help(self, ctx: commands.Context):
        pages = []

        for c in self.bot.commands:
            if type(c) == commands.HybridCommand:
                pages.append(discord.Embed(title=f"/{c.name}", description=f"{c.description}", color=discord.Color.blue()))
            elif type(c) == commands.HybridGroup:
                embed = discord.Embed(title=f"/{c.name}", color=discord.Color.blue())
                text = ""
                text += f"{c.fallback} .. {c.description}\n"
                for cc in c.commands:
                    text += f"{cc.name} .. {cc.description}\n"
                embed.description = text
                pages.append(embed)

        class Help_view(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.current_page = 0
                self.update_buttons()

            def update_buttons(self):
                self.clear_items()
                self.add_item(discord.ui.Button(emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="help_prev"))
                self.add_item(discord.ui.Button(label=f"{self.current_page + 1}/{len(pages)}", style=discord.ButtonStyle.secondary, disabled=True))
                self.add_item(discord.ui.Button(emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="help_next"))
                self.add_item(discord.ui.Button(label="セットアップ", style=discord.ButtonStyle.blurple, custom_id="help_setup"))
                self.add_item(discord.ui.Button(label="管理者用", style=discord.ButtonStyle.red, custom_id="help_owner"))

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.data["custom_id"] == "help_prev":
                    if self.current_page > 0:
                        self.current_page -= 1
                elif interaction.data["custom_id"] == "help_next":
                    if self.current_page < len(pages) - 1:
                        self.current_page += 1
                    else:
                        self.current_page = 0
                elif interaction.data["custom_id"] == "help_owner":
                    await interaction.response.edit_message(embed=discord.Embed(title="管理者用ヘルプ", description=f"""
!.gmute .. グローバルチャットでMuteします。
!.ungmute .. グローバルチャットでのMuteを解除します。
!.guilds_list .. サーバーリストを取得します。
!.guild_info .. サーバー情報を見ます。
""", color=discord.Color.red()))
                    return
                elif interaction.data["custom_id"] == "help_setup":
                    await interaction.response.edit_message(embed=discord.Embed(title="セットアップ用ヘルプ", description=f"""
グローバル宣伝を追加:
`/ads activate`
スーパーグローバルチャットを追加:
`/globalchat activate`
サーバー掲示板に乗せてみる:
`/settings register 説明:`
◀️ボタンを押したら戻れます。
""", color=discord.Color.blue()))
                    return

                self.update_buttons()
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)
                return True

        view = Help_view()
        await ctx.reply(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(CustomCog(bot))