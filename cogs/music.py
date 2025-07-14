from discord.ext import commands
import discord
import traceback
import re
import sys
import aiohttp
import json
import logging
import asyncio
from functools import partial
import time
from yt_dlp import YoutubeDL
import random

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = YoutubeDL(YTDL_OPTIONS)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> MusicCog")
    """

    @commands.group(aliases=["mu"], description="音楽関連です。")
    @commands.guild_only()
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music(self, ctx):
        await self.bot.send_subcommand(ctx, "music")

    async def get_music_info(self, url):
        loop = asyncio.get_running_loop()
        try:
            info = await loop.run_in_executor(None, partial(ytdl.extract_info, url, download=False, process=False))
            if not info:
                return None
            info["url"] = url
            info["time"] = time.time() + 60 * 60 * 24 * 7
            return info
        except Exception as e:
            print(f"Error fetching music info: {e}", file=sys.stderr)
            return None

    @music.command(name="join", aliases=["j"], description="VCに接続します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_join(self, ctx, vc: discord.VoiceChannel = None):
        if vc != None:
            try:
                await vc.connect()
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続しました。", color=discord.Color.green()))
            except:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続できませんでした。", color=discord.Color.red()))
        else:
            try:
                await ctx.author.voice.channel.connect()
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続しました。", color=discord.Color.green()))
            except:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続できませんでした。", color=discord.Color.red()))
            
    @music.command(name="leave", aliases=["l"], description="VCから退出します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_leave(self, ctx):
        try:
            await ctx.voice_client.disconnect()
            return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`から切断しました。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`から切断できませんでした", color=discord.Color.red()))

    @music.command(name="bgm", aliases=["b"], description="BGMを再生します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_bgm(self, ctx):
        try:

            if not ctx.guild.voice_client.is_playing():
                ctx.guild.voice_client.play(discord.FFmpegPCMAudio(f"data/BGM/bgm{random.randint(1, 2)}.mp3"))
                await ctx.channel.send(embed=discord.Embed(title="BGMを再生します。", color=discord.Color.green()))
            else:
                await ctx.reply("再生中です。")
        except:
            return await ctx.reply("先にBotをVCに入れてください。")
        
    @music.command(name="ussr", description="ソ連BGMを流します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_ussr(self, ctx):
        try:

            if not ctx.guild.voice_client.is_playing():
                ctx.guild.voice_client.play(discord.FFmpegPCMAudio(f"data/ussr.mp3"))
                await ctx.channel.send(embed=discord.Embed(title="ソ連国家を流します。", color=discord.Color.red()))
            else:
                await ctx.reply("再生中です。")
        except:
            return await ctx.reply("先にBotをVCに入れてください。")
        
    async def get_queue(self, guild_id):
        queue = await self.bot.async_db["Main"].Queues.find_one({"guild_id": guild_id})
        return queue or {"guild_id": guild_id, "queue": []}

    async def add_to_queue(self, guild_id, song_info):
        queue = await self.get_queue(guild_id)
        queue["queue"].append(song_info)
        await self.bot.async_db["Main"].Queues.update_one(
            {"guild_id": guild_id}, {"$set": {"queue": queue["queue"]}}, upsert=True
        )

    async def pop_from_queue(self, guild_id):
        queue = await self.get_queue(guild_id)
        if queue["queue"]:
            song = queue["queue"].pop(0)
            await self.bot.async_db["Main"].Queues.update_one(
                {"guild_id": guild_id}, {"$set": {"queue": queue["queue"]}}, upsert=True
            )
            return song
        return None

    async def play_next(self, ctx):
        song = await self.pop_from_queue(ctx.guild.id)
        if song:
            def after_playing(_):
                ctx.bot.loop.call_soon_threadsafe(self.bot.loop.create_task, self.play_next(ctx))

            if ctx.guild.voice_client:
                ctx.guild.voice_client.play(
                    discord.FFmpegOpusAudio(song["url"], bitrate=64, stderr=sys.stdout),
                    after=after_playing
                )
                await ctx.send(embed=discord.Embed(title="音楽を再生します。", description=song["title"], color=discord.Color.green()))
        else:
            if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
                return
            return

    @music.command(name="play", aliases=["p"], description="urlから音楽を再生します(一時)")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_play(self, ctx, url: str):
        try:
            info = await self.get_music_info(url)
            song = {"title": info["title"], "url": next(f["url"] for f in info["formats"] if f["ext"] == "mp4")}

            await self.add_to_queue(ctx.guild.id, song)

            if not ctx.guild.voice_client:
                await ctx.send("先にBotをVCに入れてください。")
                return

            if not ctx.guild.voice_client.is_playing():
                await self.play_next(ctx)
            else:
                await ctx.send(f"キューに追加しました: {song['title']}")
        except Exception as e:
            print(f"Error in play: {e}")
            await ctx.reply("音楽の再生に失敗しました。")

    @music.command(name="stop", aliases=["s"], description="音楽を停止します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_stop(self, ctx):
        if ctx.guild.voice_client:
            ctx.guild.voice_client.stop()
            await self.bot.async_db["Main"].Queues.update_one(
                {"guild_id": ctx.guild.id}, {"$set": {"queue": []}}, upsert=True
            )
            await ctx.send("音楽の再生を停止し、キューをクリアしました。")
        else:
            await ctx.send("現在再生中の曲はありません。")

    @music.command(name="skip", description="音楽をスキップします")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def skip(self, ctx):
        if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
            await self.play_next(ctx)
            await ctx.send("曲をスキップしました。")
        else:
            await ctx.send("現在再生中の曲はありません。")

    @commands.hybrid_group(name="tts", description="読み上げに参加します。", fallback="join")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def tts_join(self, ctx: commands.Context):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSCheck
            await ttscheck.replace_one(
                {"Channel": ctx.channel.id},
                {"Channel": ctx.channel.id},
                upsert=True
            )
            await ctx.author.voice.channel.connect()
            await ctx.reply(embed=discord.Embed(title="接続しました。", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title="接続できませんでした。", color=discord.Color.red()))
        
    @tts_join.command(name="leave", description="読み上げから脱退します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def tts_leave(self, ctx: commands.Context):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSCheck
            await ttscheck.delete_one(
                {"Channel": ctx.channel.id}
            )
            await ctx.voice_client.disconnect()
            return await ctx.reply(embed=discord.Embed(title=f"切断しました。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"切断できませんでした", color=discord.Color.red()))
        
    @tts_join.command(name="block", description="ユーザーをブロックします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def block_tts(self, ctx, member: discord.Member):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSBlock
            await ttscheck.replace_one(
                {"Guild": ctx.guild.id, "Member": member.id},
                {"Guild": ctx.guild.id, "Member": member.id},
                upsert=True
            )
            return await ctx.reply(embed=discord.Embed(title=f"{member.name}をブロックしました。", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"ブロックできませんでした。", color=discord.Color.red()))
        
    @tts_join.command(name="unblock", description="ユーザーのブロックを解除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def unblock_tts(self, ctx, member: discord.Member):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSBlock
            await ttscheck.delete_one(
                {"Guild": ctx.guild.id, "Member": member.id}
            )
            return await ctx.reply(embed=discord.Embed(title=f"{member.name}のブロックを解除しました。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"ブロックを解除ができませんでした。", color=discord.Color.red()))
        
    @tts_join.command(name="add", description="辞書に追加します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def tts_word_add(self, ctx, word1: str, word2: str):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSWord
            await ttscheck.replace_one(
                {"Guild": ctx.guild.id, "Word1": word1},
                {"Guild": ctx.guild.id, "Word1": word1, "Word2": word2},
                upsert=True
            )
            return await ctx.reply(embed=discord.Embed(title=f"辞書に追加しました。", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"辞書に追加できませんでした。", color=discord.Color.red()))
        
    @tts_join.command(name="remove", description="辞書から削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def tts_word_remove(self, ctx, word1: str):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSWord
            await ttscheck.delete_one(
                {"Guild": ctx.guild.id, "Word1": word1}
            )
            return await ctx.reply(embed=discord.Embed(title=f"辞書から削除しました。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"辞書から削除できませんでした。", color=discord.Color.red()))
        
    @tts_join.command(name="list", description="辞書を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def tts_word_list(self, ctx):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSWord
            async with ttscheck.find(filter={"Guild": ctx.guild.id}) as cursor:
                mons = await cursor.to_list(length=None)
            return await ctx.reply(embed=discord.Embed(title=f"辞書リスト", description=f"```{"\n".join([f"{m["Word1"]} - {m["Word2"]}" for m in mons])}```", color=discord.Color.green()))
        except:
            return
        
    @tts_join.command(name="voice", description="声をかえます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def tts_voice(self, ctx, コード: int):
        await ctx.defer()
        try:
            ttscheck = self.bot.async_db["Main"].TTSVoice
            await ttscheck.replace_one(
                {"Author": ctx.author.id},
                {"Author": ctx.author.id, "Voice": コード},
                upsert=True
            )
            await ctx.reply(f"声コードを{コード}にしました。")
        except:
            return
        
    @commands.Cog.listener(name="on_message")
    async def on_message_tts(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:

            return
        if not message.content:
            return
        if not message.author.voice:
            return
        if not message.guild.voice_client:
            return
        ttscheck = self.bot.async_db["Main"].TTSCheck
        try:
            ttscheckfind = await ttscheck.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if ttscheckfind is None:
            return
        ttscheck = self.bot.async_db["Main"].TTSBlock
        try:
            ttscheckfind = await ttscheck.find_one({"Guild": message.guild.id, "Member": message.author.id}, {"_id": False})
        except:
            return
        if not ttscheckfind is None:
            return
        try:
            ttsv = self.bot.async_db["Main"].TTSVoice
            try:
                ttsvfind = await ttsv.find_one({"Author": message.author.id}, {"_id": False})
            except:
                return
            if ttsvfind is None:
                if "http" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=URL"))
                if "@" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=メンション"))
                if "#" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=チャンネル"))
                if len(message.content) > 30:
                    message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=省略しました。"))
                    return
                ttscheck = self.bot.async_db["Main"].TTSWord
                async with ttscheck.find(filter={"Guild": message.guild.id}) as cursor:
                    mons = await cursor.to_list(length=None)
                c = message.content.lower()
                for m in mons:
                    c = re.sub(m["Word1"], m["Word2"], c)
                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji={c}"))
                return
            if ttsvfind["Voice"] == 0:
                if "http" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=URL"))
                if "@" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=メンション"))
                if "#" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=チャンネル"))
                if len(message.content) > 30:
                    message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=省略しました。"))
                    return
                ttscheck = self.bot.async_db["Main"].TTSWord
                async with ttscheck.find(filter={"Guild": message.guild.id}) as cursor:
                    mons = await cursor.to_list(length=None)
                c = message.content.lower()
                for m in mons:
                    c = re.sub(m["Word1"], m["Word2"], c)
                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji={c}"))
                return
            elif ttsvfind["Voice"] == 3:
                if "http" in message.content:
                    text = "URL"
                    json_data = {
                        'text': text,
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'https://plbwpbyme3.execute-api.ap-northeast-1.amazonaws.com/production/coefonts/19d55439-312d-4a1d-a27b-28f0f31bedc5/try', json=json_data) as response:
                            try:
                                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"{json.loads(await response.text())["location"]}"))
                            except:
                                return
                    return
                if "@" in message.content:
                    text = "メンション"
                    json_data = {
                        'text': text,
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'https://plbwpbyme3.execute-api.ap-northeast-1.amazonaws.com/production/coefonts/19d55439-312d-4a1d-a27b-28f0f31bedc5/try', json=json_data) as response:
                            try:
                                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"{json.loads(await response.text())["location"]}"))
                            except:
                                return
                    return
                if "#" in message.content:
                    text = "チャンネル"
                    json_data = {
                        'text': text,
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'https://plbwpbyme3.execute-api.ap-northeast-1.amazonaws.com/production/coefonts/19d55439-312d-4a1d-a27b-28f0f31bedc5/try', json=json_data) as response:
                            try:
                                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"{json.loads(await response.text())["location"]}"))
                            except:
                                return
                    return
                if len(message.content) > 40:
                    text = "省略しました。"
                    json_data = {
                        'text': text,
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'https://plbwpbyme3.execute-api.ap-northeast-1.amazonaws.com/production/coefonts/19d55439-312d-4a1d-a27b-28f0f31bedc5/try', json=json_data) as response:
                            try:
                                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"{json.loads(await response.text())["location"]}"))
                            except:
                                return
                    return
                else:

                    ttscheck = self.bot.async_db["Main"].TTSWord
                    async with ttscheck.find(filter={"Guild": message.guild.id}) as cursor:
                        mons = await cursor.to_list(length=None)
                    c = message.content.lower()
                    for m in mons:
                        c = re.sub(m["Word1"], m["Word2"], c)

                    json_data = {
                        'text': c,
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'https://plbwpbyme3.execute-api.ap-northeast-1.amazonaws.com/production/coefonts/19d55439-312d-4a1d-a27b-28f0f31bedc5/try', json=json_data) as response:
                            try:
                                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"{json.loads(await response.text())["location"]}"))
                            except:
                                return
            else:
                if "http" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=URL"))
                if "@" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=メンション"))
                if "#" in message.content:
                    return message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=チャンネル"))
                if len(message.content) > 30:
                    message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji=省略しました。"))
                    return
                ttscheck = self.bot.async_db["Main"].TTSWord
                async with ttscheck.find(filter={"Guild": message.guild.id}) as cursor:
                    mons = await cursor.to_list(length=None)
                c = message.content.lower()
                for m in mons:
                    c = re.sub(m["Word1"], m["Word2"], c)
                message.guild.voice_client.play(discord.FFmpegOpusAudio(f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji={c}"))
        except:
            return
    """

async def setup(bot):
    await bot.add_cog(MusicCog(bot))