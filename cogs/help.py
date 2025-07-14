from discord.ext import commands
import aiosqlite
import discord
import traceback
import random
import sys
import logging
import datetime
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import time
import psutil
import json

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> HelpCog")

    @commands.hybrid_group(name="bot", description="Pingを見ます。", fallback="ping")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ping_bot(self, ctx: commands.Context):
        await ctx.defer()
        start_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        msg = await self.bot.get_channel(1370283659457859665).send(f"Pingを測定しています・・\n実行者: {ctx.author.name} ({ctx.author.id})")
        end_time = msg.created_at
        latency = (end_time - start_time).total_seconds() * 1000
        await ctx.reply(embed=discord.Embed(title="Pingを測定しました。", description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms\nMessageSent: {round(latency)}ms", color=discord.Color.green()))
        await msg.reply(f"Pong!\nDiscordAPI: {round(self.bot.latency * 1000)}ms\nMessageSent: {round(latency)}ms")

    @ping_bot.command(name="about", description="Botの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def about_bot(self, ctx: commands.Context):
        await ctx.defer()
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="招待リンク", url="https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands"))
        view.add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"))
        view.add_item(discord.ui.Button(label="サーバー掲示板", url="https://www.sharkbot.xyz/server"))
        mem = self.bot.get_guild(1343124570131009579).get_role(1344470846995169310).members
        em = discord.Embed(title="`SharkBot`の情報", color=discord.Color.green())
        em.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}サーバー").add_field(name="ユーザー数", value=f"{len(self.bot.users)}人")
        cl = [c.name for c in self.bot.get_all_channels()]
        em.add_field(name="チャンネル数", value=f"{len(cl)}個")
        em.add_field(name="絵文字数", value=f"{len(self.bot.emojis)}個")
        em.add_field(name="オーナー", value=self.bot.get_user(1335428061541437531).display_name)
        em.add_field(name="モデレーター", value="\n".join([user.display_name for user in mem if not user.id == 1335428061541437531]), inline=False)
        await ctx.reply(embed=em, view=view)

    @ping_bot.command(name="permission", description="Botの持っている権限を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def permission_bot(self, ctx: commands.Context):
        await ctx.defer()
        PERMISSION_TRANSLATIONS = {
            "administrator": "管理者",
            "view_audit_log": "監査ログの表示",
            "view_guild_insights": "サーバーインサイトの表示",
            "manage_guild": "サーバーの管理",
            "manage_roles": "ロールの管理",
            "manage_channels": "チャンネルの管理",
            "kick_members": "メンバーのキック",
            "ban_members": "メンバーのBAN",
            "create_instant_invite": "招待の作成",
            "change_nickname": "ニックネームの変更",
            "manage_nicknames": "ニックネームの管理",
            "manage_emojis_and_stickers": "絵文字とステッカーの管理",
            "manage_webhooks": "Webhookの管理",
            "view_channel": "チャンネルの閲覧",
            "send_messages": "メッセージの送信",
            "send_tts_messages": "TTSメッセージの送信",
            "manage_messages": "メッセージの管理",
            "embed_links": "埋め込みリンクの送信",
            "attach_files": "ファイルの添付",
            "read_message_history": "メッセージ履歴の閲覧",
            "read_messages": "メッセージの閲覧",
            "external_emojis": "絵文字を管理",
            "mention_everyone": "everyone のメンション",
            "use_external_emojis": "外部絵文字の使用",
            "use_external_stickers": "外部ステッカーの使用",
            "add_reactions": "リアクションの追加",
            "connect": "ボイスチャンネルへの接続",
            "speak": "発言",
            "stream": "配信",
            "mute_members": "メンバーのミュート",
            "deafen_members": "メンバーのスピーカーミュート",
            "move_members": "ボイスチャンネルの移動",
            "use_vad": "音声検出の使用",
            "priority_speaker": "優先スピーカー",
            "request_to_speak": "発言リクエスト",
            "manage_events": "イベントの管理",
            "use_application_commands": "アプリケーションコマンドの使用",
            "manage_threads": "スレッドの管理",
            "create_public_threads": "公開スレッドの作成",
            "create_private_threads": "非公開スレッドの作成",
            "send_messages_in_threads": "スレッド内でのメッセージ送信",
            "use_embedded_activities": "アクティビティの使用",
            "moderate_members": "メンバーのタイムアウト",
            "use_soundboard": "サウンドボードの使用",
            "manage_expressions": "絵文字などの管理",
            "create_events": "イベントの作成",
            "create_expressions": "絵文字などの作成",
            "use_external_sounds": "外部のサウンドボードなどの使用",
            "use_external_apps": "外部アプリケーションの使用",
            "view_creator_monetization_analytics": "ロールサブスクリプションの分析情報を表示",
            "send_voice_messages": "ボイスメッセージの送信",
            "send_polls": "投票の作成",
            "external_stickers": "外部のスタンプの使用",
            "use_voice_activation": "ボイスチャンネルでの音声検出の使用"
        }
        user_perms = [PERMISSION_TRANSLATIONS.get(perm, perm) for perm, value in ctx.guild.me.guild_permissions if value]
        user_perms_str = ", ".join(user_perms)
        if not user_perms == []:
            user_perms_str = ", ".join(user_perms)
        else:
            user_perms_str = "ありません"
        not_user_perms = [PERMISSION_TRANSLATIONS.get(perm, perm) for perm, value in ctx.guild.me.guild_permissions if not value]
        if not not_user_perms == []:
            not_user_perms_str = ", ".join(not_user_perms)
        else:
            not_user_perms_str = "ありません"
        await ctx.reply(embed=discord.Embed(title=f"SharkBotの持っている権限", color=discord.Color.green()).add_field(name="許可された権限", value=user_perms_str).add_field(name="拒否された権限", value=not_user_perms_str))

    def create_bar(self, percentage, length=20):
        filled = int(percentage / 100 * length)
        return "⬛" * filled + "⬜" * (length - filled)

    async def get_system_status(self):
        loop = asyncio.get_running_loop()
        
        cpu_usage = await loop.run_in_executor(None, psutil.cpu_percent, 1)
        memory = await loop.run_in_executor(None, psutil.virtual_memory)
        disk = await loop.run_in_executor(None, psutil.disk_usage, "/")
        
        return cpu_usage, memory, disk

    async def globalchat_joined_guilds(self):
        db = self.bot.async_db["Main"].NewGlobalChat
        return await db.count_documents({})

    async def globalads_joined_guilds(self):
        db = self.bot.async_db["Main"].NewGlobalAds
        return await db.count_documents({})
    
    async def sharkaccount_user(self):
        db = self.bot.async_db["Main"].LoginData
        return await db.count_documents({})

    @ping_bot.command(name="debug", description="サーバーのステータスを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def debug_command(self, ctx: commands.Context):
        await ctx.defer()
        cpu_usage, memory, disk = await self.get_system_status()

        embed = discord.Embed(title="サーバーのシステムステータス", color=discord.Color.blue())
        embed.add_field(name="CPU 使用率", value=f"{cpu_usage}%\n{self.create_bar(cpu_usage)}", inline=False)
        memory_usage = memory.percent
        embed.add_field(name="メモリ 使用率", value=f"{memory.percent}% ({memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB)\n{self.create_bar(memory_usage)}", inline=False)
        disk_usage = disk.percent
        embed.add_field(name="ディスク 使用率", value=f"{disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n{self.create_bar(disk_usage)}", inline=False)

        globalchat_joined = await self.globalchat_joined_guilds()
        globalads_joined = await self.globalads_joined_guilds()
        embed.add_field(name="機能を使用しているサーバー数", value=f"""
グローバルチャット: {globalchat_joined}サーバー
グローバル宣伝: {globalads_joined}サーバー
""", inline=False)
        
        sharkaccount_count = await self.sharkaccount_user()
        embed.add_field(name="機能を使用しているユーザー数", value=f"""
Sharkアカウント: {sharkaccount_count}人
""", inline=False)

        await ctx.reply(embed=embed)

    async def save_bot(self, user: discord.User, bot: discord.User):
        database = self.bot.async_db["Main"].BotHistory
        await database.replace_one(
            {"Bot": bot.id,  "User": user.id}, 
            {"User": user.id, "Bot": bot.id, "BotName": bot.name}, 
            upsert=True
        )

    async def bot_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            messages = []
            async for m in self.bot.async_db["Main"].BotHistory.find({"User": interaction.user.id}):
                messages.append(m)
            choices = []

            for message in messages:
                if current.lower() in message.get("BotName").lower():
                    choices.append(discord.app_commands.Choice(name=message.get("BotName") + f"({message.get("Bot")})", value="_" + str(message.get("Bot"))))

                if len(choices) >= 25:
                    break

            if len(choices) == 0:
                return [discord.app_commands.Choice(name="履歴なし", value="0")]

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @ping_bot.command(name="invite", description="Botを招待します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @discord.app_commands.autocomplete(履歴=bot_autocomplete)
    async def invite_bot(self, ctx: commands.Context, botのid: discord.User = None, このサーバーにいるbot名: str = None, 履歴: str = None):
        if botのid:
            if not botのid.bot:
                return await ctx.reply(f"あれれ？{botのid.display_name}はBotじゃないよ？", ephemeral=True)
            await ctx.defer()
            gu = ctx.guild.default_role
            mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)
            database = self.bot.async_db["Main"].BotCredit
            embed=discord.Embed(title=f"{botのid}を招待する。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""", color=discord.Color.green())
            ver_check = "はい。このBotは認証済みです。"
            if not botのid.public_flags.verified_bot:
                ver_check = "いいえ、このBotは認証されていません。\nNukeBotの危険性があります。"
            embed.add_field(name="認証Botですか？", value=ver_check, inline=False)
            wri = await database.find({"Bot": botのid.id}).to_list(length=10)
            if not wri:
                embed.add_field(name="まだ評価されていません。", value="/bot write-bot\n評価を書いてみよう！")
            else:
                for w in wri:
                    try:
                        embed.add_field(name=f"{self.bot.get_user(w.get("User", None)).display_name}の評価", value=w.get("Reason", "まだ評価されていません。"))
                    except:
                        continue
            await self.save_bot(ctx.author, botのid)
            return await ctx.reply(embed=embed)
        if このサーバーにいるbot名:
            try:
                member = discord.utils.get(ctx.guild.members, name=このサーバーにいるbot名)
                if not member.bot:
                    return await ctx.reply(f"あれれ？{member.display_name}はBotじゃないよ？", ephemeral=True)
            except:
                return await ctx.reply(content="見つかりませんでした。", ephemeral=True)
            await ctx.defer()
            botのid = member
            gu = ctx.guild.default_role
            mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)
            database = self.bot.async_db["Main"].BotCredit
            embed=discord.Embed(title=f"{botのid}を招待する。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""", color=discord.Color.green())
            ver_check = "はい。このBotは認証済みです。"
            if not botのid.public_flags.verified_bot:
                ver_check = "いいえ、このBotは認証されていません。\nNukeBotの危険性があります。"
            embed.add_field(name="認証Botですか？", value=ver_check, inline=False)
            wri = await database.find({"Bot": botのid.id}).to_list(length=10)
            if not wri:
                embed.add_field(name="まだ評価されていません。", value="/bot write-bot\n評価を書いてみよう！")
            else:
                for w in wri:
                    try:
                        embed.add_field(name=f"{self.bot.get_user(w.get("User", None)).display_name}の評価", value=w.get("Reason", "まだ評価されていません。"))
                    except:
                        continue
            await self.save_bot(ctx.author, botのid)
            return await ctx.reply(embed=embed)
        if 履歴:
            try:
                member = self.bot.get_user(int(履歴.replace("_", "")))
                if not member.bot:
                    return await ctx.reply(f"あれれ？{member.display_name}はBotじゃないよ？", ephemeral=True)
            except:
                return await ctx.reply(content="見つかりませんでした。", ephemeral=True)
            await ctx.defer()
            botのid = member
            gu = ctx.guild.default_role
            mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)
            database = self.bot.async_db["Main"].BotCredit
            embed=discord.Embed(title=f"{botのid}を招待する。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""", color=discord.Color.green())
            ver_check = "はい。このBotは認証済みです。"
            if not botのid.public_flags.verified_bot:
                ver_check = "いいえ、このBotは認証されていません。\nNukeBotの危険性があります。"
            embed.add_field(name="認証Botですか？", value=ver_check, inline=False)
            wri = await database.find({"Bot": botのid.id}).to_list(length=10)
            if not wri:
                embed.add_field(name="まだ評価されていません。", value="/bot write-bot\n評価を書いてみよう！")
            else:
                for w in wri:
                    try:
                        embed.add_field(name=f"{self.bot.get_user(w.get("User", None)).display_name}の評価", value=w.get("Reason", "まだ評価されていません。"))
                    except:
                        continue
            await self.save_bot(ctx.author, botのid)
            return await ctx.reply(embed=embed)
        await ctx.reply("""
# SharkBotの招待リンクです。
https://discord.com/oauth2/authorize?client_id=1322100616369147924
        """)

    @ping_bot.command(name="write-bot", description="Botに評価を付けます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def write_bot(self, ctx: commands.Context, botのid: discord.User, 評価: str):
        if botのid.id == self.bot.user.id:
            return await ctx.reply("SharkBotの評価は書けません。", ephemeral=True)
        if not botのid.bot:
            return await ctx.reply("Botではありません。", ephemeral=True)
        await ctx.defer()
        database = self.bot.async_db["Main"].BotCredit
        await database.replace_one(
            {"Bot": botのid.id,  "User": ctx.author.id}, 
            {"User": ctx.author.id, "Bot": botのid.id, "Reason": 評価}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Botの評価を書きました。", color=discord.Color.green()))

    async def get_prefix(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].CustomPrefixBot
        p = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        if not p:
            return "!."
        return p["Prefix"]

    @ping_bot.command(name="me-setting", description="SharkBotの名前を取得・設定するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def me_setting(self, ctx: commands.Context, 名前: str = None):
        await ctx.defer()
        if not 名前:
            return await ctx.reply(embed=discord.Embed(title="私の名前", description=f"名前: {ctx.guild.me.display_name}", color=discord.Color.green()).add_field(name="埋め込めるテキスト", value="-prefix- .. Prefixを埋め込みます", inline=False))
        pre = await self.get_prefix(ctx)
        mem = await ctx.guild.me.edit(nick=名前.replace("-prefix-", pre))
        await ctx.reply("<:Success:1362271281302601749> 名前を設定しました。")

    @ping_bot.command(name="suggotion", description="sharkbotに提案します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def suggotion_bot(self, ctx: commands.Context, 提案内容: str):
        await ctx.defer()
        await self.bot.get_channel(1368202518181449819).send(embed=discord.Embed(title=f"{ctx.author.name}({ctx.author.id})\nからの提案", color=discord.Color.green(), description=提案内容))
        await ctx.reply(embed=discord.Embed(title="SharkBotに提案しました。", description="提案内容は公式サーバーに送信されます。\nよろしくお願いします。", color=discord.Color.green()))

    @ping_bot.command(name="shark", description="SharkNetworkについて見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def shark_network(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="`SharkNetwork`の情報", description=f"""SharkNetworkについて。
SharkNetworkは、
以下のサービスを運営しております。
・`SharkBot` .. だれにでも使いやすいDiscordBot
ぜひご利用ください。
        """, color=discord.Color.green()))

    @ping_bot.command(name="follow", description="お知らせチャンネルをフォローします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def ann_bot_follow(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        await self.bot.get_channel(1344234727388872765).follow(destination=ctx.channel)
        await self.bot.get_channel(1347451795978453052).follow(destination=ctx.channel)
        await asyncio.sleep(1)
        await self.bot.get_channel(1361592624817111150).follow(destination=ctx.channel)
        await self.bot.get_channel(1361173338763956284).follow(destination=ctx.channel)
        await ctx.reply(embed=discord.Embed(title="フォローしました。", color=discord.Color.green()))

    @ping_bot.command(name="setup", description="セットアップをします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def setup_help(self, ctx: commands.Context):
        class page(discord.ui.View):
            def __init__(self, bot, ctx: commands.Context, db):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.db = db
                self.bot = bot
                self.automod_flag = False
    
            @discord.ui.button(label="あとで", style=discord.ButtonStyle.red)
            async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await interaction.message.edit(embed=discord.Embed(title="中止しました。", description="再度実行したい場合は、\n`/bot setup`を実行してください。", color=discord.Color.red()), view=None)

            @discord.ui.button(label="次", style=discord.ButtonStyle.blurple)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.message.embeds[0].title == "セットアップをしましょう！":
                    await interaction.response.defer(ephemeral=True)
                    await interaction.message.edit(embed=discord.Embed(title="サーバー掲示板に載せる", description="`/settings register 説明:`で載せられます。", color=discord.Color.blue()))
                elif interaction.message.embeds[0].title == "サーバー掲示板に載せる":
                    await interaction.response.defer(ephemeral=True)
                    await interaction.message.edit(embed=discord.Embed(title="セットアップが完了しました。", description="ありがとうございます。", color=discord.Color.green()), view=None)

        await ctx.reply(embed=discord.Embed(title="セットアップをしましょう！", description="""1. サーバー掲示板に載せる
""", color=discord.Color.blue()), view=page(self.bot, ctx, self.bot.async_db["Main"]))

async def setup(bot):
    await bot.add_cog(HelpCog(bot))