from discord.ext import commands
from discord import app_commands
import discord
import traceback
import sys
import logging
import random
import datetime
import time
import asyncio
from discord import Webhook
import aiohttp

class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> LoggingCog")

    async def get_logging_webhook(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].EventLoggingChannel
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind.get("Webhook", None)
    
    async def get_logging_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].EventLoggingChannel
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind.get("Channel", None))

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_log(self, message: discord.Message):
        try:
            wh = await self.get_logging_webhook(message.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> メッセージが削除されました", description=f"{message.content}", color=discord.Color.red()).set_footer(text=f"mid:{message.id}").set_author(name=f"{message.author.name}", icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url))
        except Exception as e:
            return

    @commands.Cog.listener("on_member_ban")
    async def on_member_ban_log(self, guild: discord.Guild, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> メンバーがBANされました", description=f"{member.mention}\nメンバーがBANされました: {datetime.datetime.now()}", color=discord.Color.red()).set_footer(text=f"uid:{member.id}").set_author(name=f"{member.name}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url))
        except:
            return
        
    @commands.Cog.listener("on_member_update")
    async def on_member_update_log(self, before: discord.Member, after: discord.Member):
        try:
            if before.display_name == after.display_name:
                return
            wh = await self.get_logging_webhook(after.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Edit:1367039517868953600> メンバーが編集されました", description=f"編集前の名前: {before.display_name}\nメンバーの編集時間: {datetime.datetime.now()}\n編集後の名前: {after.display_name}", color=discord.Color.yellow()).set_footer(text=f"uid:{after.id}").set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url))
        except:
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_timeout_log(self, before: discord.Member, after: discord.Member):
        try:
            wh = await self.get_logging_webhook(after.guild)
            if not wh:
                return

            if before.timed_out_until is None and after.timed_out_until is not None:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> メンバーがタイムアウトされました。", description=f"メンバー: {after.mention}", color=discord.Color.green()).set_footer(text=f"uid:{after.id}").set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url))
        except:
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_role_log(self, before: discord.Member, after: discord.Member):
        try:
            before_roles = set(before.roles)
            after_roles = set(after.roles)

            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles

            wh = await self.get_logging_webhook(after.guild)
            if not wh:
                return

            if added_roles:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> ロールが追加されました", description=f"メンバー: {after.mention}\nロール: {'\n'.join([rr.mention for rr in added_roles])}", color=discord.Color.green()).set_footer(text=f"uid:{after.id}").set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url))

            if removed_roles:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> ロールが削除されました", description=f"メンバー: {after.mention}\nロール: {'\n'.join([rr.mention for rr in removed_roles])}", color=discord.Color.red()).set_footer(text=f"uid:{after.id}").set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url))
        except:
            return

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_log(self, before: discord.Message, after: discord.Message):
        try:
            if after.author.id == self.bot.user.id:
                return
            if after.content == "":
                return
            if before.content == after.content:
                return
            wh = await self.get_logging_webhook(after.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Edit:1367039517868953600> メッセージが編集されました", description=f"編集前:\n{before.content}\n編集後:\n{after.content}", color=discord.Color.yellow()).set_footer(text=f"mid:{after.id}").set_author(name=f"{after.author.name}", icon_url=after.author.avatar.url if after.author.avatar else after.author.default_avatar.url))
        except:
            return
        
    @commands.Cog.listener("on_guild_channel_create")
    async def on_guild_channel_create_log(self, channel: discord.abc.GuildChannel):
        try:
            wh = await self.get_logging_webhook(channel.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> チャンネルが作成されました", description=f"名前: {channel.name}\n作成時間: {channel.created_at}", color=discord.Color.green()).set_footer(text=f"cid:{channel.id}"))
        except:
            return
        
    @commands.Cog.listener("on_guild_channel_delete")
    async def on_guild_channel_delete_log(self, channel: discord.abc.GuildChannel):
        try:
            wh = await self.get_logging_webhook(channel.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> チャンネルが削除されました", description=f"名前: {channel.name}", color=discord.Color.red()).set_footer(text=f"cid:{channel.id}"))
        except:
            return
        
    @commands.Cog.listener("on_invite_create")
    async def on_invite_create_log(self, invite: discord.Invite):
        try:
            wh = await self.get_logging_webhook(invite.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> 招待リンクが作成されました", description=f"チャンネル: {invite.channel.name}\n招待リンク作成時間: {datetime.datetime.now()}\nurl: {invite.url}", color=discord.Color.green()).set_footer(text=f"invid:{invite.id}").set_author(name=f"{invite.inviter.name}", icon_url=invite.inviter.avatar.url if invite.inviter.avatar else invite.inviter.default_avatar.url))
        except:
            return

    @commands.Cog.listener("on_guild_role_create")
    async def on_guild_role_create_log(self, role: discord.Role):
        try:
            wh = await self.get_logging_webhook(role.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> ロールが作成されました", description=f"名前: {role.name}", color=discord.Color.green()).set_footer(text=f"rid:{role.id}"))
        except:
            return
        
    @commands.Cog.listener("on_guild_role_delete")
    async def on_guild_role_delete_log(self, role: discord.Role):
        try:
            wh = await self.get_logging_webhook(role.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> ロールが削除されました", description=f"名前: {role.name}", color=discord.Color.red()).set_footer(text=f"rid:{role.id}"))
        except:
            return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_log(self, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(member.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Plus:1367039505865113670> メンバーが参加しました", description=f"名前: {member.name}\nアカウント作成日: {member.created_at}\n参加時間: {datetime.datetime.now()}", color=discord.Color.green()).set_footer(text=f"mid:{member.id}").set_author(name=f"{member.name}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url))
        except:
            return
        
    @commands.Cog.listener("on_member_remove")
    async def on_member_remove_log(self, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(member.guild)
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:Minus:1367039494322262096> メンバーが退出しました", description=f"名前: {member.name}\nアカウント作成日: {member.created_at}\n参加時間: {datetime.datetime.now()}", color=discord.Color.red()).set_footer(text=f"mid:{member.id}").set_author(name=f"{member.name}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url))
        except:
            return

    @commands.hybrid_group(name="logging", description="ログの設定をします。", fallback="setup")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def logging_setup(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].EventLoggingChannel
        web = await ctx.channel.create_webhook(name="SharkBot-Log")
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id, "Webhook": web.url}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ログをセットアップしました。", color=discord.Color.green()))

    @logging_setup.command(name="disable", description="ログを無効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def logging_disable(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].EventLoggingChannel
        await db.delete_one({"Guild": ctx.guild.id})
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ログを無効化しました。", color=discord.Color.green()))

    @logging_setup.command(name="sendlog", description="ログを送信します")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def logging_sendlog(self, ctx: commands.Context, 内容: str):
        wh = await self.get_logging_webhook(ctx.guild)
        if not wh:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ログを送信できませんでした。", color=discord.Color.red()))
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(wh, session=session)
            await webhook_.send(avatar_url=self.bot.user.avatar.url, embed=discord.Embed(title="<:idea:1367052508396130335> ログが送信されました", description=内容, color=discord.Color.blue()).set_author(name=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url))
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ログを送信しました。", color=discord.Color.green()))

    @logging_setup.command(name="logsearch", description="最新のログを検索します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    @app_commands.choices(内容=[
        app_commands.Choice(name='メッセージ削除',value="delete"),
        app_commands.Choice(name='メンバー参加',value="join")
    ])
    async def logging_search(self, ctx: commands.Context, 内容: app_commands.Choice[str]):
        await ctx.defer()
        channel = await self.get_logging_channel(ctx.guild)
        if not channel:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> チャンネルが見つかりませんでした。", color=discord.Color.red()))
        async for c_l in channel.history(limit=100):
            if not c_l.embeds:
                continue
            if 内容.value == "delete":
                if c_l.embeds[0].title == "<:Minus:1367039494322262096> メッセージが削除されました":
                    if not c_l.embeds[0].description:
                        return await ctx.reply(embed=discord.Embed(title="このサーバーで最後に削除されたメッセージ", color=discord.Color.green()))
                    return await ctx.reply(embed=discord.Embed(title="このサーバーで最後に削除されたメッセージ", description=c_l.embeds[0].description, color=discord.Color.green()).set_author(name=c_l.embeds[0].author.name, icon_url=c_l.embeds[0].author.icon_url))
            elif 内容.value == "join":
                if c_l.embeds[0].title == "<:Plus:1367039505865113670> メンバーが参加しました":
                    if not c_l.embeds[0].description:
                        return await ctx.reply(embed=discord.Embed(title="このサーバーで最後に参加したユーザー", color=discord.Color.green()))
                    return await ctx.reply(embed=discord.Embed(title="このサーバーで最後に参加したユーザー", description=c_l.embeds[0].description, color=discord.Color.green()).set_author(name=c_l.embeds[0].author.name, icon_url=c_l.embeds[0].author.icon_url))
        return await ctx.reply(embed=discord.Embed(title="見つかりませんでした。", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))