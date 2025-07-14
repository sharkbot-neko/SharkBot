from discord.ext import commands, tasks
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import re
import json
from discord import Webhook
from functools import partial
import urllib.parse
import time
import aiohttp

COOLDOWN_TIMEGC = 5
user_last_message_timegc = {}
user_last_message_time_ad = {}

user_last_message_time_mute = {}

cooldown_transfer = {}

class GlobalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> GlobalCog")

    async def check_edit_ticket(self, message: discord.Message):
        try:
            db = self.bot.async_db["Main"].SharkPoint
            user_data = await db.find_one({"_id": message.author.id})
            if user_data and user_data.get("editnick", 0) != 0:
                return True
            else:
                return False
        except:
            return False

    async def user_block(self, message: discord.Message):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return False
        if not dbfind is None:
            return True
        return False

    async def get_guild_emoji(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            if dbfind is None:
                return "😎"
            return dbfind.get("Emoji", "😎")
        except Exception as e:
            return "😎"

    async def send_one_join_globalchat(self, webhook: str, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(title=f"{ctx.guild.name}が参加したよ！よろしく！", description=f"オーナーID: {ctx.guild.owner_id}\nコマンド実行者: {ctx.author.display_name}/({ctx.author.id})", color=discord.Color.green())
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")

    async def send_global_chat_join(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        tasks = []
        async for channel in channels:
            if channel["Channel"] == ctx.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                tasks.append(self.send_one_join_globalchat(channel["Webhook"], ctx))
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})

        if tasks:
            await asyncio.gather(*tasks)

    async def send_one_leave_globalchat(self, webhook: str, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(title=f"{ctx.guild.name}が抜けちゃったよ・・", description=f"オーナーID: {ctx.guild.owner_id}\nコマンド実行者: {ctx.author.display_name}/({ctx.author.id})", color=discord.Color.red())
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")

    async def send_global_chat_leave(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        tasks = []
        async for channel in channels:
            if channel["Channel"] == ctx.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                tasks.append(self.send_one_leave_globalchat(channel["Webhook"], ctx))
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})

        if tasks:
            await asyncio.gather(*tasks)

    async def globalchat_join(self, ctx: commands.Context):
        web = await ctx.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "GuildName": ctx.guild.name, "Webhook": web.url}, 
            upsert=True
        )
        return True
    
    async def globalchat_join_newch(self, channel: discord.TextChannel):
        web = await channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.replace_one(
            {"Guild": channel.guild.id}, 
            {"Guild": channel.guild.id, "Channel": channel.id, "GuildName": channel.guild.name, "Webhook": web.url}, 
            upsert=True
        )
        return True
    
    async def globalchat_leave(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.delete_one({
            "Guild": ctx.guild.id
        })
        return True

    async def globalchat_leave_channel(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.delete_one({
            "Channel": ctx.channel.id
        })
        return True
    
    async def globalchat_check(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChat
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False
        
    async def globalchat_check_channel(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False

    def filter_global(self, message: discord.Message) -> bool:
        blocked_words = ["discord.com", "discord.gg", "x.gd", "shorturl.asia", "tiny.cc", "<sound:", "niga", "everyone", "here"]
        return not any(word in message.content for word in blocked_words)

    async def badge_build(self, message: discord.Message):
        if message.author.id == 1335428061541437531:
            return "👑"

        try:

            if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(message.author.id).roles:
                return "🛠️"
        except:
            return "😀"

        return "😀"

    async def send_one_globalchat(self, webhook: str, message: discord.Message, ref_msg: discord.Message = None):
        if not self.filter_global(message):
            return

        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.avatar.url)
            else:
                embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.default_avatar.url)
            if not message.attachments == []:
                embed.add_field(name="添付ファイル", value=message.attachments[0].url)

            if ref_msg:
                wh = ref_msg.webhook_id
                embed_ = ref_msg.embeds
                if wh:
                    try:
                        name = embed_[0].author.name.replace("[👑]", "").replace("[😀]", "").replace("[🛠️]", "").split("/")[0]
                        value = embed_[0].description
                    except:
                        name = ref_msg.author.name
                        value = ref_msg.content
                else:
                    name = ref_msg.author.name
                    value = ref_msg.content
                embed.add_field(name=name, value=value)
            try:
                await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global", allowed_mentions=discord.AllowedMentions.none())
            except:
                return

    async def send_global_chat(self, message: discord.Message, ref_msg: discord.Message = None):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await self.send_one_globalchat(channel["Webhook"], message, ref_msg)
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})
            
            await asyncio.sleep(1)

    async def send_one_globalchat_selectbot(self, webhook: str, bot: discord.User):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=f"{bot.display_name}", title="ランダムなBotが選択されました！", color=discord.Color.blue())
            embed.set_footer(text=f"ランダムなBot")
            embed.set_thumbnail(url=bot.avatar.url if bot.avatar else bot.default_avatar.url)

            embed.set_author(name=f"ランダムなBot/{bot.id}", icon_url=self.bot.user.avatar.url)
            await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")

    async def send_global_chat_room(self, room: str, message: discord.Message, ref_msg: discord.Message = None):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        channels = db.find({"Name": room})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await self.send_one_globalchat(channel["Webhook"], message, ref_msg)
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})
            
            await asyncio.sleep(1)

    async def globalchat_room_check(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return dbfind.get("Name", None)
        except Exception as e:
            return False

    async def globalchat_room_join(self, ctx: commands.Context, roomname: str):
        web = await ctx.channel.create_webhook(name="SharkBot-GlobalRoom")
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "GuildName": ctx.guild.name, "Webhook": web.url, "Name": roomname}, 
            upsert=True
        )
        return True
    
    async def globalchat_room_leave(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        await db.delete_one({
            "Guild": ctx.guild.id, "Channel": ctx.channel.id
        })
        return True

    @commands.hybrid_group(name="global", description="グローバルチャットに参加・脱退します。", fallback="join")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_join(self, ctx: commands.Context, 部屋名: str = None):
        await ctx.defer()
        if not 部屋名:
            if ctx.guild.member_count < 20:
                return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
            check_room = await self.globalchat_room_check(ctx)
            if check_room:
                await self.globalchat_room_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            check = await self.globalchat_check(ctx)
            if check:
                await self.globalchat_leave(ctx)
                await self.send_global_chat_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.globalchat_join(ctx)
                await self.send_global_chat_join(ctx)
                await ctx.reply(embed=discord.Embed(title="グローバルチャットに参加しました。", description="グローバルチャットのルール\n・荒らしをしない\n・宣伝をしない\n・r18やグロ関連のものを貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。", color=discord.Color.green()))
        
        else:
            check = await self.globalchat_room_check(ctx)
            if check:
                await self.globalchat_room_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.globalchat_room_join(ctx, 部屋名)
                await ctx.reply(embed=discord.Embed(title="グローバルチャットに参加しました。", color=discord.Color.green()))
        
    @global_join.command(name="leave", description="グローバルチャットから脱退します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_leave(self, ctx: commands.Context):
        await ctx.defer()
        await self.globalchat_leave_channel(ctx)
        await self.globalchat_room_leave(ctx)
        await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))

    async def set_emoji_guild(self, emoji: str, guild:discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        await db.replace_one(
            {"Guild": guild.id}, 
            {"Guild": guild.id, "Emoji": emoji}, 
            upsert=True
        )

    @global_join.command(name="emoji", description="グローバルチャットのサーバーごとの絵文字を設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_emoji(self, ctx: commands.Context, 絵文字: str):
        await ctx.defer()
        if len(絵文字) > 3:
            return await ctx.reply("絵文字は3文字まででお願いします。")
        await self.set_emoji_guild(絵文字, ctx.guild)
        await ctx.reply(embed=discord.Embed(title="絵文字を変更しました。", color=discord.Color.green()).add_field(name="絵文字", value=絵文字))

    @global_join.command(name="create", description="グローバルチャットのチャンネルを新規作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_create(self, ctx: commands.Context):
        await ctx.defer()
        cat = ctx.channel.category
        if not cat:
            ch = await ctx.guild.create_text_channel(name="shark-global")
        else:
            ch = await cat.create_text_channel(name="shark-global")
        await self.globalchat_join_newch(ch)
        await ctx.reply(embed=discord.Embed(title="チャンネルを作成しました！", description=f"{ch.jump_url}", color=discord.Color.green()))

    @global_join.command(name="server", description="サーバー掲示板を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def global_server(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="サーバー掲示板", description="以下のurlからアクセスできます。\nhttps://www.sharkbot.xyz/server", color=discord.Color.blue()))

    @global_join.command(name="register", description="サーバー掲示板に登録します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def global_register(self, ctx: commands.Context, 説明: str):
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

    async def get_reg(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Register
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind.get("Invite", "NoneInvite") + "\n" + dbfind.get("Description", "NoneDescription")

    @global_join.command(name="transfer", description="サーバー掲示板からグローバル宣伝に転送します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def global_transfer(self, ctx: commands.Context):
        await ctx.defer()
        reg = await self.get_reg(ctx)
        if not reg:
            return await ctx.reply(ephemeral=True, content="転送失敗！\nサーバー掲示板に登録してないよ！")
        if ctx.guild.icon == None:
            return await ctx.reply("転送をするにはサーバーアイコンを設定する必要があります。")
        current_time = time.time()
        last_message_time = cooldown_transfer.get(ctx.guild.id, 0)
        if current_time - last_message_time < 7200:
            return await ctx.reply(embed=discord.Embed(title="転送失敗・・", description="グローバル宣伝に転送するには2時間待つ必要があります。", color=discord.Color.red()))
        cooldown_transfer[ctx.guild.id] = current_time
        db = self.bot.async_db["Main"].NewGlobalAds
        channels = db.find({})

        async for channel in channels:

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await self.send_one_ads_message(channel["Webhook"], ctx, reg)
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})
            
            await asyncio.sleep(1)

        return await ctx.reply(embed=discord.Embed(title="転送完了！", description="グローバル宣伝に転送されたよ！", color=discord.Color.green()).set_thumbnail(url=ctx.guild.icon.url))

    async def sgc_make_json(self, message: discord.Message):
            dic = {}

            dic.update({"type": "message"})
            dic.update({"userId": str(message.author.id)})
            dic.update({"userName": message.author.name})
            dic.update({"x-userGlobal_name": message.author.global_name})
            dic.update({"userDiscriminator": message.author.discriminator})
            if hasattr(message.author.avatar, 'key'):
                dic.update({"userAvatar": message.author.avatar.key})
            else:
                dic.update({"userAvatar": None})
            dic.update({"isBot": message.author.bot})
            dic.update({"guildId": str(message.guild.id)})
            dic.update({"guildName": message.guild.name})
            if hasattr(message.guild.icon, 'key'):
                dic.update({"guildIcon": message.guild.icon.key})
            else:
                dic.update({"guildIcon": None})
            dic.update({"channelId": str(message.channel.id)})
            dic.update({"channelName": message.channel.name})
            dic.update({"messageId": str(message.id)})
            dic.update({"content": message.content.replace('@', '＠')})

            if message.attachments != []:
                arr = []
                for attachment in message.attachments:
                    arr.append(attachment.url)
                dic.update({"attachmentsUrl": arr})

            jsondata = json.dumps(dic, ensure_ascii=False)

            return jsondata

    async def send_super_global_chat_room(self, message: discord.Message, ref_msg: discord.Message = None):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        channels = db.find()

        async with aiohttp.ClientSession() as session:
            async for channel in channels:
                if channel["Channel"] == message.channel.id:
                    continue

                target_channel = self.bot.get_channel(channel["Channel"])
                
                if target_channel:
                    embed = discord.Embed(description=message.content, color=discord.Color.blue())
                    embed.set_footer(text=f"mID:{message.id} / SharkBot")
                    bag = await self.badge_build(message)
                    if message.author.avatar:
                        embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.avatar.url)
                    else:
                        embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.default_avatar.url)
                    if not message.attachments == []:
                        embed.add_field(name="添付ファイル", value=message.attachments[0].url)
                    webhook_ = Webhook.from_url(channel.get("Webhook", None), session=session)
                    await webhook_.send(embed=embed, username="SharkBot-SGC", avatar_url=self.bot.user.avatar.url)
                    await asyncio.sleep(1)

    async def super_join_global_chat(self, ctx: commands.Context):
        wh = await ctx.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "GuildName": ctx.guild.name, "Webhook": wh.url},
            upsert=True
        )

    async def super_leave_global_chat(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        await db.delete_one({
            "Guild": ctx.guild.id
        })
        return True
    
    async def super_globalchat_check(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False
        
    async def super_globalchat_check_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False

    @commands.Cog.listener("on_message")
    async def on_message_superglobal_getjson(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if not message.channel.id == 707158257818664991:
            return
        
        try:
            dic = json.loads(message.content)
        except json.decoder.JSONDecodeError as e:
            return

        if "type" in dic and dic["type"] != "message":
            return

        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():

                target_channel = self.bot.get_channel(ch["Channel"])
                if target_channel:
                    embed = discord.Embed(description=dic["content"], color=discord.Color.blue())
                    embed.set_footer(text=f"mID:{dic['messageId']} / {message.author.display_name}")
                    bag = await self.badge_build(message)
                    if dic["userAvatar"]:
                        embed.set_author(name=f"[{bag}] {dic['userName']}/{dic['userId']}", icon_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]))
                    else:
                        embed.set_author(name=f"[{bag}] {dic['userName']}/{dic['userId']}", icon_url=message.author.default_avatar.url)
                    if not dic.get("attachmentsUrl") == []:
                        try:
                            embed.add_field(name="添付ファイル", value=dic["attachmentsUrl"][0])
                        except:
                            pass
                    webhook_ = Webhook.from_url(ch.get("Webhook", None), session=session)
                    await webhook_.send(embed=embed, username="SharkBot-SGC", avatar_url=self.bot.user.avatar.url)
                    await asyncio.sleep(1)
        await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_super_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return
        
        if "!." in message.content:
            return

        check = await self.super_globalchat_check_message(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        js = await self.sgc_make_json(message)
        await self.bot.get_channel(707158257818664991).send(content=js, allowed_mentions=discord.AllowedMentions.none())

        await self.send_super_global_chat_room(message)
        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")

    """
        @global_join.command(name="sgc", description="スーパーグローバルチャットに参加・脱退します。")
        @commands.cooldown(2, 10, commands.BucketType.guild)
        @commands.has_permissions(manage_channels=True)
        async def sgc_join_leave(self, ctx: commands.Context):
            await ctx.defer()
            if ctx.guild.member_count < 20:
                return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
            check = await self.super_globalchat_check(ctx)
            if check:
                await self.super_leave_global_chat(ctx)
                return await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.super_join_global_chat(ctx)
                await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットに参加しました。", color=discord.Color.green()))
    """

    @global_join.command(name="sgc", description="スーパーグローバルチャットに参加・脱退します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_sgc(self, ctx: commands.Context):
        await ctx.defer()
        if ctx.guild.member_count < 20:
            return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
        check = await self.super_globalchat_check(ctx)
        if check:
            await self.super_leave_global_chat(ctx)
            return await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットから脱退しました。", color=discord.Color.green()))
        else:
            await self.super_join_global_chat(ctx)
            await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットに参加しました。", color=discord.Color.green()))

    @global_join.command(name="sgc-info", description="スーパーグローバルチャットに参加しているBot一覧を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def global_sgc_info(self, ctx: commands.Context):
        await ctx.defer()
        res = ""
        rl = self.bot.get_guild(706905953320304772).get_role(773868241713627167)
        async for m in self.bot.get_guild(706905953320304772).fetch_members():
            if not m.bot:
                continue
            if m.id == 1343156909242454038:
                continue
            if rl in m.roles:
                res += f"[{m.display_name}](https://discord.com/oauth2/authorize?client_id={m.id}&permissions=8&integration_type=0&scope=bot+applications.commands)\n"
        await ctx.reply(embed=discord.Embed(title="SGCのBot情報", color=discord.Color.green(), description=res))

    @commands.hybrid_command(name="globalchat", description="グローバルチャットに参加・脱退します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_chat(self, ctx: commands.Context, 部屋名: str = None):
        await ctx.defer()
        if not 部屋名:
            check_room = await self.globalchat_room_check(ctx)
            if check_room:
                await self.globalchat_room_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            if ctx.guild.member_count < 20:
                return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
            check = await self.globalchat_check(ctx)
            if check:
                await self.globalchat_leave(ctx)
                await self.send_global_chat_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.globalchat_join(ctx)
                await self.send_global_chat_join(ctx)
                await ctx.reply(embed=discord.Embed(title="グローバルチャットに参加しました。", description="グローバルチャットのルール\n・荒らしをしない\n・宣伝をしない\n・r18やグロ関連のものを貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。", color=discord.Color.green()))
        
        else:
            check = await self.globalchat_room_check(ctx)
            if check:
                await self.globalchat_room_leave(ctx)
                return await ctx.reply(embed=discord.Embed(title="グローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.globalchat_room_join(ctx, 部屋名)
                await ctx.reply(embed=discord.Embed(title="グローバルチャットに参加しました。", color=discord.Color.green()))
        
    async def globalads_check(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalAds
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False

    async def globalads_join(self, ctx: commands.Context):
        web = await ctx.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalAds
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "GuildName": ctx.guild.name, "Webhook": web.url}, 
            upsert=True
        )
        return True
    
    async def globalads_leave(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].NewGlobalAds
        await db.delete_one({
            "Guild": ctx.guild.id
        })
        return True

    async def globalads_check_channel(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalAds
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception as e:
            return False

    async def send_one_ads_message(self, webhook: str, ctx: commands.Context, text: str):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=text, color=discord.Color.blue())
            em = await self.get_guild_emoji(ctx.guild)
            embed.set_footer(text=f"[{em}] {ctx.guild.name}/{ctx.guild.id}")

            bag = await self.badge_build(ctx)

            if ctx.author.avatar:
                embed.set_author(name=f"[{bag}] {ctx.author.name}/{ctx.author.id}", icon_url=ctx.author.avatar.url)
            else:
                embed.set_author(name=f"[{bag}] {ctx.author.name}/{ctx.author.id}", icon_url=ctx.author.default_avatar.url)
            try:
                await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")
            except:
                return

    async def send_one_ads(self, webhook: str, message: discord.Message):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=message.content, color=discord.Color.blue())
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.avatar.url)
            else:
                embed.set_author(name=f"[{bag}] {message.author.name}/{message.author.id}", icon_url=message.author.default_avatar.url)
            if not message.attachments == []:
                embed.add_field(name="添付ファイル", value=message.attachments[0].url)
            try:
                await webhook_.send(embed=embed, avatar_url=self.bot.user.avatar.url, username="SharkBot-Global")
            except:
                return

    async def send_global_ads(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalAds
        channels = db.find({})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await self.send_one_ads(channel["Webhook"], message)
            else:
                print(f"{channel['Channel']} が見つからないため削除します。")
                await db.delete_one({"Channel": channel["Channel"]})
            
            await asyncio.sleep(1)

    @commands.hybrid_command(name="globalads", description="グローバル宣伝に参加・脱退します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def global_ads(self, ctx: commands.Context):
        await ctx.defer()
        if ctx.guild.member_count < 20:
            return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
        check = await self.globalads_check(ctx)
        if check:
            await self.globalads_leave(ctx)
            return await ctx.reply(embed=discord.Embed(title="グローバル宣伝から脱退しました。", color=discord.Color.green()))
        else:
            await self.globalads_join(ctx)
            await ctx.reply(embed=discord.Embed(title="グローバル宣伝に参加しました。", description="グローバル宣伝のルール\n・荒らし系を貼らない\n・r18やグロ関連のものを貼らない\n・sh0p系を貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。", color=discord.Color.green()))

    async def add_sharkpoint(self, ctx: commands.Context, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": ctx.author.id})
        if user_data:
            await db.update_one({"_id": ctx.author.id}, {"$inc": {"count": coin}})
            return True
        else:
            await db.insert_one({"_id": ctx.author.id, "count": coin})
            return True

    @commands.Cog.listener("on_message")
    async def on_message_global_alert(self, message: discord.Message):
        if not message.channel.id == 1362296899259863112:
            return
        await self.send_global_chat(message)

    @commands.Cog.listener("on_message")
    async def on_message_ads(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalads_check_channel(message)

        if not check:
            return
        
        block = await self.user_block(message)

        if block:
            return
        
        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")        

        await self.send_global_ads(message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_globalroom(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalchat_room_check(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")        

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat_room(check, message, rmsg)
        else:
            await self.send_global_chat_room(check, message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalchat_check_channel(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")        

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat(message, rmsg)
        else:
            await self.send_global_chat(message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(GlobalCog(bot))