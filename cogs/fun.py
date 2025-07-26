import aiofiles.os
from discord.ext import commands
from discord import Webhook
import io
import discord
import textwrap
import math
import io
import traceback
from discord import app_commands
from tempfile import NamedTemporaryFile
import time
import sys
import pykakasi
import aiofiles
from datetime import datetime, timedelta, timezone
import base64
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
import logging
import asyncio
from functools import partial
from urllib.parse import quote
import textwrap
import aiohttp
import json
import io
from PIL import ImageFont, Image, ImageDraw, ImageSequence
import random
import unicodedata
import ssl
from bs4 import BeautifulSoup
import requests
import MeCab

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width=40, new_height=40):
    return image.resize((new_width, new_height))

def grayify(image):
    return image.convert("L")

def pixels_to_ascii(image):
    pixels = image.getdata()
    ascii_str = ""
    for pixel in pixels:
        ascii_str += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return ascii_str

def image_to_ascii(image_path):
    try:
        image = Image.open(image_path)
    except Exception as e:
        return "変換エラー"

    image = resize_image(image)
    image = grayify(image)

    ascii_str = pixels_to_ascii(image)

    ascii_art = "\n".join(ascii_str[i:i+40] for i in range(0, len(ascii_str), 40))
    return ascii_art

def text_len_sudden(text):
    count = 0
    for c in text:
        count += 2 if unicodedata.east_asian_width(c) in 'FWA' else 1
    return count

def sudden_generator(msg):
    length = text_len_sudden(msg)
    generating = '＿人'
    for i in range(length//2):
        generating += '人'
    generating += '人＿\n＞  ' + msg + '  ＜\n￣^Y'
    for i in range(length//2):
        generating += '^Y'
    generating += '^Y￣'
    return generating

cooldown_miqmod_time = {}
cooldown_miqrec_time = {}

async def get_random_meme():
    url = "https://meme-api.com/gimme/wholesomememes"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            if response.status == 200:
                js = await response.json()
                if not js["nsfw"]:
                    return js["url"]
                else:
                    return "NSFW meme detected, skipping."
            return None

def generate_chat_image(messages: list[dict]) -> io.BytesIO:
    font_username = ImageFont.truetype("data/DiscordFont.ttf", 24)
    font_message = ImageFont.truetype("data/DiscordFont.ttf", 20)
    font_timestamp = ImageFont.truetype("data/DiscordFont.ttf", 16)

    background_color = (54, 57, 63)
    username_color = (88, 101, 242)
    text_color = (255, 255, 255)
    timestamp_color = (185, 187, 190)

    def get_circular_avatar(url, size=(48, 48)):
        response = requests.get(url)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA").resize(size)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        avatar.putalpha(mask)
        return avatar

    def wrap_text(text, font, draw, max_width):
        lines = []
        current_line = ''
        for char in text:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        return lines

    max_text_width = 700
    padding = 20
    line_spacing = 8
    avatar_size = (48, 48)
    text_start_x = 80

    dummy_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy_img)

    total_height = padding
    rendered_messages = []

    for msg in messages:
        lines = wrap_text(msg["message"], font_message, draw, max_text_width)
        height = len(lines) * (font_message.size + line_spacing) + 30
        rendered_messages.append((msg, lines, height))
        total_height += height + padding

    image_width = max_text_width + text_start_x + padding
    img = Image.new("RGBA", (image_width, total_height), background_color)
    draw = ImageDraw.Draw(img)

    y = padding
    for msg, lines, height in rendered_messages:
        avatar = get_circular_avatar(msg["avatar_url"], avatar_size)
        img.paste(avatar, (padding, y + 5), avatar)

        draw.text((text_start_x, y), msg["username"], font=font_username, fill=username_color)
        name_width = draw.textbbox((0, 0), msg["username"], font=font_username)[2]
        draw.text((text_start_x + name_width + 8, y + 3), msg["timestamp"], font=font_timestamp, fill=timestamp_color)

        y += 30
        for line in lines:
            draw.text((text_start_x, y), line, font=font_message, fill=text_color)
            y += font_message.size + line_spacing

        y += padding

    draw.text((text_start_x, y), line, font=font_message, fill=text_color)

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output

async def check_nsfw(image_bytes):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("image", image_bytes, filename="image.jpg", content_type="image/jpeg")

        async with session.post("http://192.168.11.26:3000/analyze", data=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result
            else:
                return {"safe": False}

class UnShort():
    def __init__(self):
        self.session = requests.Session()
        pass

    def run(self, word: str):
        self.html = self.session.get(f"https://seoi.net/ryaku/{word}").text
        bs4 = BeautifulSoup(self.html, 'html.parser')
        return bs4.find({"p": {"class": "div_desc"}}).get_text().replace("「", "").replace(f"{word}」は", "").replace("」の略だと予想されます。", "")

async def fetch_avatar(user: discord.User):
    if user.avatar:
        url_a = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar.key}"
    else:
        url_a = user.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(url_a, timeout=10) as resp:
            return await resp.read()

def wrap_text_with_ellipsis(text, font, draw, max_width, max_height, line_height):
    lines = []
    for raw_line in text.split("\n"):
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char

            if len(lines) * line_height >= max_height - line_height * 2:
                ellipsis = "…"
                while True:
                    bbox = draw.textbbox((0, 0), current_line + ellipsis, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        break
                    if len(current_line) == 0:
                        break
                    current_line = current_line[:-1]
                lines.append(current_line + ellipsis)
                return lines

        if current_line:
            lines.append(current_line)

    return lines

def create_quote_image(author, text, avatar_bytes, background, textcolor, color: bool):
        width, height = 800, 400
        background_color = background
        text_color = textcolor

        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)

        avatar_size = (400, 400)
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize(avatar_size)

        mask = Image.new("L", avatar_size, 255)
        for x in range(avatar_size[0]):
            alpha = 255 if x < avatar_size[0] // 2 else int(255 * (1 - (x - avatar_size[0] // 2) / (avatar_size[0] / 2)))
            for y in range(avatar_size[1]):
                mask.putpixel((x, y), alpha)
        avatar.putalpha(mask)

        img.paste(avatar, (0, height - avatar_size[1]), avatar)

        try:
            font = ImageFont.truetype("data/DiscordFont.ttf", 30)
            name_font = ImageFont.truetype("data/DiscordFont.ttf", 20)
        except:
            font = ImageFont.load_default()
            name_font = ImageFont.load_default()

        text_x = 420
        max_text_width = width - text_x - 50

        max_text_height = height - 80
        line_height = font.size + 10

        lines = wrap_text_with_ellipsis(text, font, draw, max_text_width, max_text_height, line_height)

        total_lines = len(lines)
        line_height = font.size + 10
        text_block_height = total_lines * line_height
        text_y = (height - text_block_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            draw.text(
                ((width + text_x - 50 - line_width) // 2, text_y + i * line_height),
                line,
                fill=text_color,
                font=font
            )

        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=name_font)
        author_width = bbox[2] - bbox[0]
        author_x = (width + text_x - 50 - author_width) // 2
        author_y = text_y + len(lines) * line_height + 10

        draw.text((author_x, author_y), author_text, font=name_font, fill=text_color)

        draw.text((580, 0), "FakeQuote - SharkBot", font=name_font, fill=text_color)

        if color:

            return img
        else:
            return img.convert("L")

def convert_emoji(emoji: bytes):
    io_ = io.BytesIO(emoji)
    image = Image.open(io_).resize((500, 500))
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    io_.close()
    rd = output.read()
    output.close()
    return rd

async def sync_to_async(func):
    return await asyncio.to_thread(func)

class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.imageaikey = self.tkj["ImageAIAPIKey"]
        self.tagger = MeCab.Tagger()
        print(f"init -> FunCog")

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
                    return response_data.get("content", "No content in response")

        except aiohttp.ClientError as e:
            return f"Network error occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    @commands.hybrid_group(name="fun", description="ランダムな色を生成します。", fallback="random_color")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def random_color(self, ctx: commands.Context):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        await ctx.reply(embed=discord.Embed(title="ランダムな色", color=discord.Color.from_rgb(r, g, b), description=f"""
r: {r}
g: {g}
b: {b}
"""))

    @random_color.command(name="suddendeath", description="突然の死を生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def suddendeath(self, ctx: commands.Context, 言葉: str):
        await ctx.defer()
        msg = await ctx.reply(embed=discord.Embed(title="突然の死", description=f"```{sudden_generator(言葉)}```", color=discord.Color.green()))

    @random_color.command(name="janken", description="じゃんけんをします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def janken(self, ctx: commands.Context):
        bot = random.choice(["ぐー", "ちょき", "ぱー"])
        def check(user: str, bot: str):
            if user == bot:
                return "あいこです\nもう一回やってみる？"
            if user == "ぐー" and bot == "ちょき":
                return "あなたの勝ち\nもう一回やってみる？"
            if user == "ちょき" and bot == "ぱー":
                return "あなたの勝ち\nもう一回やってみる？"
            if user == "ぱー" and bot == "ぐー":
                return "あなたの勝ち\nもう一回やってみる？"
            return "Botの勝ち\nもう一回チャレンジしてね！"
        class AnsView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

            @discord.ui.button(label="ぐー", style=discord.ButtonStyle.blurple)
            async def goo(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if ctx.author.id != interaction.user.id:
                    return await interaction.followup.send(ephemeral=True, content="あなたのボタンではありません。")
                await interaction.message.edit(view=None, embed=discord.Embed(title="じゃんけん", description=f"あなた: {button.label}\nBot: {bot}\n\n" + check(button.label, bot), color=discord.Color.blue()))

            @discord.ui.button(label="ちょき", style=discord.ButtonStyle.blurple)
            async def choki(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if ctx.author.id != interaction.user.id:
                    return await interaction.followup.send(ephemeral=True, content="あなたのボタンではありません。")
                await interaction.message.edit(view=None, embed=discord.Embed(title="じゃんけん", description=f"あなた: {button.label}\nBot: {bot}\n\n" + check(button.label, bot), color=discord.Color.blue()))

            @discord.ui.button(label="ぱー", style=discord.ButtonStyle.blurple)
            async def par(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if ctx.author.id != interaction.user.id:
                    return await interaction.followup.send(ephemeral=True, content="あなたのボタンではありません。")
                await interaction.message.edit(view=None, embed=discord.Embed(title="じゃんけん", description=f"あなた: {button.label}\nBot: {bot}\n\n" + check(button.label, bot), color=discord.Color.blue()))

            @discord.ui.button(label="あきらめる", style=discord.ButtonStyle.red)
            async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if ctx.author.id != interaction.user.id:
                    return await interaction.followup.send(ephemeral=True, content="あなたのボタンではありません。")
                await interaction.message.edit(view=None, embed=discord.Embed(title="じゃんけん", description="Botの勝ち\nもう一回チャレンジしてね！", color=discord.Color.blue()))

        await ctx.reply(embed=discord.Embed(title="じゃんけん", description="""
・グーはチョキに勝ち、パーに負けます
・チョキはパーに勝ち、グーに負けます
・パーはグーに勝ち、チョキに負けます
同じ手を両者が出した場合は、あいことなります。
""", color=discord.Color.blue()), view=AnsView())

    @random_color.command(name="keigo", description="敬語に変換します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def keigp(self, ctx: commands.Context, 口語: str):
        await ctx.defer()
        hen = await self.keigo_trans(口語) 
        await ctx.reply(embed=discord.Embed(title="三秒敬語", description=f"{hen}", color=discord.Color.green()))

    @random_color.command(name="unshort", description="短縮ワードを展開します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.is_nsfw()
    async def unshort(self, ctx: commands.Context, ワード: str):
        await ctx.defer()
        loop = asyncio.get_event_loop()
        word = await loop.run_in_executor(None, partial(UnShort().run, ワード))
        await ctx.reply(embed=discord.Embed(title="短縮ワード展開", description=f"{word}", color=discord.Color.green()))

    @random_color.command(name="retranslate", description="何回も翻訳をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def retranslate(self, ctx: commands.Context, ワード: str):
        if not ctx.interaction:
            msg = await ctx.reply(embed=discord.Embed(title="何回も翻訳 (ja)", description=f"ja -> {ワード}", color=discord.Color.green()))
        else:
            msg = await ctx.channel.send(embed=discord.Embed(title="何回も翻訳 (ja)", description=f"ja -> {ワード}", color=discord.Color.green()))
            await ctx.reply(ephemeral=True, content="翻訳を開始します。。")
        loop = asyncio.get_event_loop()
        word = ワード
        for _ in ["en", "zh-CN", "ko", "ru", "ja"]:
            await asyncio.sleep(3)
            translator = await loop.run_in_executor(None, partial(GoogleTranslator, source="auto", target=_))
            word = await loop.run_in_executor(None, partial(translator.translate, word))
            msg = await msg.edit(embed=discord.Embed(title=f"何回も翻訳 ({_})", description=f"{msg.embeds[0].description}\n{_} -> {word}", color=discord.Color.green()))
        await asyncio.sleep(3)
        msg = await msg.edit(embed=discord.Embed(title=f"何回も翻訳", description=f"{msg.embeds[0].description}\n完了しました。", color=discord.Color.green()))

    @random_color.command(name="text-to-emoji", description="テキストを絵文字にします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def text_to_emoji(self, ctx: commands.Context, ワード: str):
        await ctx.defer()
        async def text_emoji(text):
            kakasi = pykakasi.kakasi()
            result = kakasi.convert(text)
                
            def text_to_discord_emoji(text):
                emoji_map = {chr(97 + i): chr(0x1F1E6 + i) for i in range(26)}
                num_emoji_map = {str(i): f"{i}️⃣" for i in range(10)}
                return [emoji_map[char.lower()] if char.isalpha() else num_emoji_map[char] if char.isdigit() else None for char in text if char.isalnum()]
            
            romaji_text = "".join(item["kunrei"] for item in result if "kunrei" in item)
            emojis = text_to_discord_emoji(romaji_text)

            return emojis

        ems = await text_emoji(ワード[:20])
        await ctx.reply(" ".join(ems))

    @random_color.command(name="clap", description="手をたたきます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def clap(self, ctx: commands.Context, テキスト: str):
        await ctx.defer()
        def extract_words(text):
            parsed = self.tagger.parse(text)
            lines = parsed.splitlines()
            words = [line.split('\t')[0] for line in lines if '\t' in line]
            return words
        await ctx.reply(embed=discord.Embed(title="手をたたく", description=f'{"👏".join(extract_words(テキスト))}👏', color=discord.Color.green()))

    @random_color.command(name="emoji-list", description="絵文字リストを出力します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def emoji_list(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        for start in range(0, len(ctx.guild.emojis), 17):
            await ctx.channel.send(content=" ".join([s.__str__() for s in ctx.guild.emojis[start : start + 17]]))
            await asyncio.sleep(1)
        await ctx.reply(ephemeral=True, content="✅絵文字を出力しました。")

    @commands.Cog.listener("on_message")
    async def on_message_lovecalc_mention(self, message: discord.Message):
        if message.author.bot:
            return

        try:

            for user in message.mentions:
                query = {
                    "author_id": message.author.id,
                    "target_id": user.id
                }
                update = {
                    "$inc": {"count": 1},
                    "$setOnInsert": {
                        "author_name": message.author.name,
                        "target_name": user.name
                    }
                }
                await self.bot.async_db["Main"].LoveCalcMention.update_one(query, update, upsert=True)
        except:
            return

    @random_color.command(name="lovecalc", description="恋愛度計算機を使用します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def love_calc(self, ctx: commands.Context, 相手: discord.User):
        await ctx.defer()
        record = await self.bot.async_db["Main"].LoveCalcMention.find_one({
            "author_id": ctx.author.id,
            "target_id": 相手.id
        })
        def calculate_score(mentions):
            if mentions == 0:
                return 0
            score = math.log(mentions + 1, 5) * 18
            return min(int(score), 100)
        mentions = record["count"] if record else 0
        score = calculate_score(mentions)
        word = ""
        if score > 80:
            word = "✨完璧な相性！運命の相手かも！？✨"
        elif score > 50:
            word = "😊いい感じ！もう少し距離を縮めてみよう！"
        elif score > 30:
            word = "😅少し努力が必要かも…？"
        else:
            word = "🙈あまり相性がよくないかも。でも諦めないで！"
        await ctx.reply(embed=discord.Embed(title="恋愛度計算機", description=f"{ctx.author.mention} ❤️ {相手.mention} の恋愛度は... {score}% です！\n{word}", color=discord.Color.green()))

    @random_color.command(name="ascii", description="アスキーアートを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ascii_art(self, ctx: commands.Context, ファイル: discord.Attachment):
        await ctx.defer()
        rd = await ファイル.read()
        io_ = io.BytesIO(rd)
        io_.seek(0)
        text = image_to_ascii(io_)
        st = io.StringIO(text)
        await ctx.reply(file=discord.File(st, "ascii.txt"))
        st.close()
        io_.close()

    @random_color.command(name="ishiba", description="石破の声を作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ishiba_make(self, ctx: commands.Context, テキスト: str):
        await ctx.defer()
        encoded_text = quote(テキスト, encoding="utf-8")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:5002/ishiba?text={encoded_text}") as q:
                try:
                    f = await q.read()
                    file_data = io.BytesIO(f)
                    file_data.seek(0)
                    embed = discord.Embed(title="石破の声", color=discord.Color.green())
                    await ctx.reply(embed=embed, file=discord.File(file_data, "ishiba.mp3"))
                except UnicodeDecodeError as e:
                    await ctx.reply(f"音声ファイルの読み込み中にエラーが発生しました。\n{e}")

    @random_color.command(name="roll", description="さいころをふります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def roll(self, ctx: commands.Context, 何面か: int):
        await ctx.reply(f"🎲 {ctx.author.mention}: {random.randint(1, 何面か)}")

    @random_color.command(name="magickblock", description="面白いことが起きるブロックを開けます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def magickblock(self, ctx: commands.Context):
        lucks = [
            ("大量のTNT", "https://fukafuka295.jp/wp-content/uploads/2020/02/minecraft-lucky-block-mod-25-768x432.jpg.webp"),
            ("大量のアイテム", "https://fukafuka295.jp/wp-content/uploads/2020/02/minecraft-lucky-block-mod-8-768x432.jpg.webp"),
            ("帯電クリーパー", "https://fukafuka295.jp/wp-content/uploads/2020/02/minecraft-lucky-block-mod-26-768x432.jpg.webp"),
            ("数種類の馬", "https://fukafuka295.jp/wp-content/uploads/2020/02/minecraft-lucky-block-mod-7-768x432.jpg.webp"),
        ]
        choices = random.choice(lucks)
        await ctx.reply(embed=discord.Embed(title=choices[0], color=discord.Color.yellow()).set_image(url=choices[1]).set_footer(text="画像元サイト: fukafuka295.jp").set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url))

    @random_color.command(name="tanabata", description="七夕の短冊を作成しました。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tanabata(self, ctx: commands.Context, 願い事: str):
        res = "```★┷┓\n"
        for t in 願い事:
            res += "┃" + t + "┃\n"
        res += "┗━★```"
        await ctx.reply(embed=discord.Embed(title="短冊", description=res, color=discord.Color.green())
                        .set_footer(text="http://tanzaku-maker.rhp.ninja-x.jp/"))

    @commands.hybrid_group(name="image", description="猫を取得します。", fallback="cat")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def cat_image(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search?size=med&mime_types=jpg&format=json&has_breeds=true&order=RANDOM&page=0&limit=1") as cat:
                msg = await ctx.reply(embed=discord.Embed(title="猫の画像", color=discord.Color.green()).set_image(url=json.loads(await cat.text())[0]["url"]))

    @cat_image.command(name="dog", description="犬を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def dog_image(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as dog_:
                await ctx.reply(embed=discord.Embed(title="犬の画像", color=discord.Color.green()).set_image(url=f"{json.loads(await dog_.text())["message"]}"))

    @cat_image.command(name="meme", description="ミームを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def meme_get(self, ctx: commands.Context):
        await ctx.defer()
        url = await get_random_meme()
        await ctx.reply(url)

    @cat_image.command(name="5000", description="5000兆円ほしい！")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choen_5000(self, ctx: commands.Context, 上: str, 下: str, noアルファ: bool = None):
        if noアルファ:
            if noアルファ == False:
                msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}"))
            else:
                msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}&noalpha=true"))
        else:
            msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}"))

    @cat_image.command(name="textmoji", description="テキストを絵文字にします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(色=[
        app_commands.Choice(name='赤',value="FF0000"),
        app_commands.Choice(name='青',value="1111FF"),
        app_commands.Choice(name='黒',value="000000"),
    ])
    async def textmoji(self, ctx: commands.Context, 色: app_commands.Choice[str], テキスト: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://emoji-gen.ninja/emoji?align=center&back_color=00000000&color={色.value.upper()}FF&font=notosans-mono-bold&locale=ja&public_fg=true&size_fixed=true&stretch=true&text={テキスト}") as resp:
                i = io.BytesIO(await resp.read())
                await ctx.reply(file=discord.File(i, "emoji.png"))

    @cat_image.command(name="catbomb", description="猫の画像をたくさん出します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def catbomb(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search?limit=10") as cat:
                js = await cat.json()
                urls = ""
                for j in js:
                    urls += f"{j.get("url", "")}\n"
                await ctx.reply(f"{urls}")

    @cat_image.command(name="httpcat", description="httpcatを出します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def httpcat(self, ctx: commands.Context, ステータスコード: int):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="HTTPCat", color=discord.Color.blue()).set_image(url=f"https://http.cat/{ステータスコード}").set_footer(text="Httpcat", icon_url="https://i.imgur.com/6mKRXgR.png"))

    @cat_image.command(name="monstr", description="モンストのガチャを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def monstr(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        base = Image.open("data/gacha.jpg").convert("RGBA")
        if ユーザー.avatar:
            try:
                read = await ユーザー.avatar.replace(size=256).read()
            except Exception:
                read = await ユーザー.default_avatar.replace(size=256).read()
        else:
            read = await ユーザー.default_avatar.replace(size=256).read()
        with io.BytesIO(read) as read_:
            avatar = Image.open(read_).convert("RGBA").resize((423, 411))
            paste_position = (150, 385)
            background_part = base.crop((
                paste_position[0], paste_position[1],
                paste_position[0] + avatar.width, paste_position[1] + avatar.height
            ))
            avatar_with_bg = Image.alpha_composite(background_part, avatar)
            mask = Image.new("L", avatar_with_bg.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, avatar_with_bg.width, avatar_with_bg.height), fill=255)
            avatar_with_bg.putalpha(mask)
            base.paste(avatar_with_bg, paste_position, avatar_with_bg)
        with io.BytesIO() as save_:
            base.save(save_, format="PNG", optimize=True)
            save_.seek(0)
            file = discord.File(save_, "gacha.jpg")
            await ctx.reply(file=file)

    @cat_image.command(name="progress", description="Minecraftの進捗画像を生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def progress(self, ctx: commands.Context, テキスト: str):
        await ctx.defer()
        base = Image.open("data/progress.png")
        draw = ImageDraw.Draw(base)
        font = ImageFont.truetype('data/MinecraftFont.ttf', 30)
        draw.text((120, 70), テキスト, '#FFFFFF', font=font)
        save_ = io.BytesIO()
        base.save(save_, format="PNG")
        save_.seek(0)
        await ctx.reply(file=discord.File(save_, "gacha.png"))
        save_.close()

    @cat_image.command(name="neko", description="猫耳を生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.is_nsfw()
    async def neko(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nekobot.xyz/api/image?type=neko") as response:
                res = await response.json()
                e = discord.Embed(color=res["color"], title="NekoAPI (猫耳)")
                e.set_image(url=res["message"])
                await ctx.reply(embed=e)

    @cat_image.command(name="kemomimi", description="ケモミミを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.is_nsfw()
    async def kemomimi(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nekobot.xyz/api/image?type=kemonomimi") as response:
                res = await response.json()
                e = discord.Embed(color=res["color"], title="NekoAPI (ケモミミ)")
                e.set_image(url=res["message"])
                await ctx.reply(embed=e)

    @cat_image.command(name="food", description="食べ物を生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def food(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nekobot.xyz/api/image?type=food") as response:
                res = await response.json()
                e = discord.Embed(color=res["color"], title="NekoAPI (食べ物)")
                e.set_image(url=res["message"])
                await ctx.reply(embed=e)

    async def get_user_tag(self, user: discord.User):
        db = self.bot.async_db["Main"].UserTag
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return "称号なし"
        if dbfind is None:
            return "称号なし"
        return dbfind["Tag"]

    @cat_image.command(name="profile", description="プロフィールを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def profile(self, ctx: commands.Context, 自己紹介文: str):
        await ctx.defer()

        data = aiohttp.FormData()

        if ctx.author.avatar:
            avatar_bytes = io.BytesIO(await ctx.author.avatar.read())
        else:
            avatar_bytes = io.BytesIO(await ctx.author.default_avatar.read())
        avatar_bytes.seek(0)

        data.add_field(
            name='avatar',
            value=avatar_bytes,
            filename='avatar.png',
            content_type='image/png'
        )

        tag = await self.get_user_tag(ctx.author)

        data.add_field('name', ctx.author.name)
        data.add_field('id', str(ctx.author.id))
        data.add_field('bio', "\n".join(textwrap.wrap(自己紹介文, 20)))
        data.add_field('tag', tag[:4])

        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:5002/profile", data=data) as resp:
                if resp.status != 200:
                    await ctx.reply(f"エラーが発生しました: {resp.status}")
                    return

                image_bytes = io.BytesIO(await resp.read())
                image_bytes.seek(0)
                file = discord.File(image_bytes, "profile.png")
                await ctx.reply(file=file)

    @cat_image.command(name="miq", description="Make it a quoteを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(色=[
        app_commands.Choice(name='カラー',value="color"),
        app_commands.Choice(name='白黒',value="black")
    ])
    @app_commands.choices(背景色=[
        app_commands.Choice(name='黒',value="black"),
        app_commands.Choice(name='白',value="white")
    ])
    async def make_it_a_quote(self, ctx: commands.Context, ユーザー: discord.User, 発言: str, 色: app_commands.Choice[str], 背景色: app_commands.Choice[str]):
        await ctx.defer()
        class MiqButton(discord.ui.View):
            def __init__(self, timeout=180):
                super().__init__(timeout=timeout)

            @discord.ui.button(emoji="<:Delete:1362275962967953570>", style=discord.ButtonStyle.gray)
            async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if not ctx.author.id == interaction.user.id:
                    return
                await interaction.message.edit(content=f"<:Success:1362271281302601749> 削除しました。", view=None, attachments=[])
        avatar = ユーザー
        av = await fetch_avatar(avatar)
        if 色.value == "color":
            color = True
        else:
            color = False
        if 背景色.value == "black":
            back = (0, 0, 0)
            text = (255, 255, 255)
        elif 背景色.value == "white":
            back = (255, 255, 255)
            text = (0, 0, 0)
        miq = create_quote_image(
            ユーザー.display_name,
            発言,
            av,
            back,
            text,
            color
        )
        image_binary = io.BytesIO()
        miq.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename='fake_quote.png')
        await ctx.reply(file=file, view=MiqButton(), content=f"{len(image_binary.getvalue())} bytes")
        image_binary.close()

    @cat_image.command(name="roulette", description="ルーレットを生成します。ワードは,で区切ってください。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def roulette(self, ctx: commands.Context, ワード: str):
        await ctx.defer()
        size = 500
        center = (size // 2, size // 2)
        radius = size // 2
        sectors = ワード.split(",")
        colors = ["red", "green", "blue", "yellow", "purple", "orange"]

        try:
            font = ImageFont.truetype("data/DiscordFont.ttf", 20)
        except:
            font = ImageFont.load_default()

        executor = ThreadPoolExecutor()

        async def generate_frame(offset_angle, highlight_index=None, highlight=False):
            def create_frame():
                img = Image.new("RGBA", (size, size), "white")
                draw = ImageDraw.Draw(img)

                angle_per_sector = 360 / len(sectors)
                start_angle = offset_angle

                for i, label in enumerate(sectors):
                    end_angle = start_angle + angle_per_sector

                    if highlight_index is not None and i == highlight_index:
                        fill_color = "gold" if highlight else colors[i % len(colors)]
                    else:
                        fill_color = colors[i % len(colors)]

                    draw.pieslice([0, 0, size, size], start=start_angle, end=end_angle, fill=fill_color)

                    angle = (start_angle + end_angle) / 2
                    rad = math.radians(angle)

                    text_radius = radius * 0.65
                    text_x = center[0] + text_radius * math.cos(rad)
                    text_y = center[1] + text_radius * math.sin(rad)

                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]

                    draw.text(
                        (text_x - text_w / 2, text_y - text_h / 2),
                        label,
                        fill="black",
                        font=font
                    )

                    start_angle = end_angle

                draw.ellipse(
                    [size*0.3, size*0.3, size*0.7, size*0.7],
                    fill="white"
                )
                return img

            return await asyncio.get_running_loop().run_in_executor(executor, create_frame)

        frame_count = 60
        initial_speed = 20
        deceleration = 0.95

        rotation_speeds = []
        current_speed = initial_speed
        for _ in range(frame_count):
            rotation_speeds.append(current_speed)
            current_speed *= deceleration

        offset_angle = 0
        tasks = []

        for speed in rotation_speeds:
            tasks.append(generate_frame(offset_angle))
            offset_angle += speed

        frames = await asyncio.gather(*tasks)

        final_angle = offset_angle % 360
        angle_per_sector = 360 / len(sectors)
        winning_index = random.randint(0, len(sectors) - 1)

        flash_times = 6
        flash_duration = 100

        for i in range(flash_times):
            highlight = (i % 2 == 0)
            frames.append(await generate_frame(offset_angle, highlight_index=winning_index, highlight=highlight))

        file_path = f"temp/{ctx.author.id}_{random.randint(0, 999)}_roulette.gif"

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, partial(frames[0].save, file_path,save_all=True,append_images=frames[1:],optimize=False,duration=50,loop=0))
            file = discord.File(file_path, "roulette.gif")
            await ctx.reply(file=file, embed=discord.Embed(description=f"「{sectors[winning_index]}」が当たりました。", color=discord.Color.blue()))
        finally:
            check = await aiofiles.os.path.isfile(file_path)
            if check:
                try:
                    await aiofiles.os.remove(file_path)
                except OSError as e:
                    pass

        executor.shutdown()

    @cat_image.command(name="events-calendar", description="イベントカレンダーを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def events_calendar(self, ctx: commands.Context):
        await ctx.defer()
        
        events = await ctx.guild.fetch_scheduled_events()
        def gen(events):
            today = datetime.today()

            try:
                font = ImageFont.truetype("data/DiscordFont.ttf", 20)
            except:
                font = ImageFont.load_default()

            one_week_later = datetime.now(timezone.utc) + timedelta(days=7)

            ls = {}

            dates = []
            for i in range(7):
                day = today + timedelta(days=i)
                ls[day.strftime('%d')] = []
                dates.append((day.strftime('%d'), day.month))

            img = Image.new("RGBA", (400, 330), "white")

            draw = ImageDraw.Draw(img)

            co = 0

            draw.text((10, 10), f"{dates[0][1]}月", '#000000', font=font)

            upcoming_events = [
                event for event in events
                if event.start_time and datetime.now(timezone.utc) <= event.start_time <= one_week_later
            ]

            for ue in upcoming_events:
                ls[ue.start_time.strftime('%d')].append(ue.name)

            for date_str, month in dates:
                ebe = ls.get(date_str, [])
                if ebe == []:
                    draw.text((10, 50+co), f"{date_str}日: イベントなし", '#000000', font=font)
                else:
                    draw.text((10, 50+co), f"{date_str}日: {", ".join(ebe)}", '#000000', font=font)
                co+=30

            return img

        img = await asyncio.get_running_loop().run_in_executor(None, partial(gen, events))

        with io.BytesIO() as save_:
            img.save(save_, format="PNG", optimize=True)
            save_.seek(0)
            await ctx.reply(file=discord.File(save_, "calendar.png"))

    @cat_image.command(name="chatsave", description="チャットを画像化してセーブします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def chatsave(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)

        if not ctx.interaction:
            return await ctx.reply("スラッシュコマンド専用です。")

        messages = []
        async for msg in ctx.channel.history(limit=1):
            messages.append({
                "username": msg.author.display_name,
                "message": msg.content.replace("\n", ""),
                "timestamp": msg.created_at.strftime("今日 %H:%M"),
                "avatar_url": msg.author.display_avatar.url
            })

        img_data = await asyncio.to_thread(generate_chat_image, messages)

        file = discord.File(img_data, filename="chat.png")
        await ctx.channel.send(file=file)
        await ctx.reply("✅", ephemeral=True)

    @cat_image.command(name="emojiadd", description="絵文字を追加します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_emojis=True)
    async def emoji_add(self, ctx: commands.Context, 画像: discord.Attachment):
        await ctx.defer()
        image = await 画像.read()
        em = await asyncio.to_thread(convert_emoji, image)
        emoji = await ctx.guild.create_custom_emoji(name=画像.filename.split(".")[0], image=em)
        await ctx.reply(embed=discord.Embed(title="絵文字を追加しました。", color=discord.Color.green()))
        await ctx.channel.send(content=emoji.__str__())

    @cat_image.command(name="robokasu", description="ロボかすを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def robokasu(self, ctx: commands.Context, テキスト: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:5002/robokasu?text={テキスト}") as resp:
                i = io.BytesIO(await resp.read())
                await ctx.reply(file=discord.File(i, "robo.png"))

    @cat_image.command(name="emoji-layer", description="絵文字を重ねます")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.is_nsfw()
    async def emoji_layer(self, ctx: commands.Context, 絵文字1: discord.Emoji, 絵文字2: discord.Emoji):
        await ctx.defer()
        em1 = await 絵文字1.read()
        check_one = await check_nsfw(em1)
        if not check_one["safe"]:
            return await ctx.reply(embed=discord.Embed(title="その絵文字は使用できません。", color=discord.Color.red()))
        em2 = await 絵文字2.read()
        check_two = await check_nsfw(em2)
        if not check_two["safe"]:
            return await ctx.reply(embed=discord.Embed(title="その絵文字は使用できません。", color=discord.Color.red()))
        def create_image(em, em_2):
            img1 = Image.open(io.BytesIO(em)).convert("RGBA")
            img2 = Image.open(io.BytesIO(em_2)).convert("RGBA")
            base_size = (256, 256)
            img1 = img1.resize(base_size, Image.LANCZOS)
            img2 = img2.resize(base_size, Image.LANCZOS)
            stacked = Image.new("RGBA", base_size)
            stacked.paste(img1, (0, 0), img1)
            stacked.paste(img2, (0, 0), img2)
            buffer = io.BytesIO()
            stacked.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        img = await asyncio.get_running_loop().run_in_executor(None, partial(create_image, em1, em2))
        files = await asyncio.get_running_loop().run_in_executor(None, partial(discord.File, img, filename="emoji_layer.png"))
        await ctx.reply(file=files, embed=discord.Embed(title="絵文字を重ねました", color=discord.Color.green()))

    @cat_image.command(name="nounai", description="脳内メーカーで遊びます")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nounai(self, ctx: commands.Context, 名前: str):
        await ctx.reply(embed=discord.Embed(title="脳内メーカー", color=discord.Color.green()).set_image(url=f"https://maker.usoko.net/nounai/img/{名前}.gif"))

    @cat_image.command(name="kakeizu", description="家系図を作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def kakeizu(self, ctx: commands.Context, 名前: str):
        await ctx.reply(embed=discord.Embed(title="家系図", color=discord.Color.green()).set_image(url=f"https://usokomaker.com/kakeizu_fantasy/r/img/{名前}.gif"))

async def setup(bot):
    await bot.add_cog(FunCog(bot))