from discord.ext import commands
import discord
import asyncio
from deep_translator import GoogleTranslator
from functools import partial
import datetime

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        async def lang_get(guild: discord.Guild, word: str):
            db = self.bot.async_db["Main"].GuildLang
            try:
                dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            except:
                return word
            if dbfind is None:
                return word
            if dbfind["Lang"] == "en":
                if word == "はい":
                    return "yes"
                if word == "いいえ":
                    return "no"
                if word == "います。":
                    return "I am."
                if word == "いません。":
                    return "not here."
                if word == "ユーザー":
                    return "User"
                if word == "モデレーター":
                    return "Moderator"
                if word == "管理者":
                    return "Admin"
                if word == "ログイン情報":
                    return "Login Information"
                if word == "基本情報":
                    return "Base Information"
                if word == "その他APIからの情報":
                    return "Other API information"
                if word == "言語を設定しました。":
                    return "The language has been set."
                if word == "寄付かSharkBotをたくさん導入することでSharkポイントがたまります。":
                    return "You can earn Shark Points by donating or introducing a lot of SharkBots."
                loop = asyncio.get_event_loop()
                translator = await loop.run_in_executor(None, partial(GoogleTranslator, source="auto", target="en"))
                translated_text = await loop.run_in_executor(None, partial(translator.translate, word))
                return translated_text
            else:
                return word
        self.bot.lang_get = lang_get
        def convert_day(dt: datetime.datetime):
            JST = datetime.timezone(datetime.timedelta(hours=9))
            dt.astimezone(JST)
            tstr = dt.strftime('%Y年%m月%d日')
            return tstr
        def convert_time(dt: datetime.datetime):
            JST = datetime.timezone(datetime.timedelta(hours=9))
            dt.astimezone(JST)
            tstr = dt.strftime('%H時%M分%S秒')
            return tstr
        def convert_date(dt: datetime.datetime):
            JST = datetime.timezone(datetime.timedelta(hours=9))
            dt.astimezone(JST)
            tstr = dt.strftime('%Y年%m月%d日 %H時%M分%S秒')
            return tstr
        self.bot.convert_day = convert_day
        self.bot.convert_time = convert_time
        self.bot.convert_data = convert_date
        print(f"init -> TranslateCog")

async def setup(bot):
    await bot.add_cog(TranslateCog(bot))