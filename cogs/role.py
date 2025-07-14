from discord.ext import commands
import datetime
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import re
from functools import partial
import time

class RGBModal(discord.ui.Modal, title="🎨 RGBを入力してください。"):
    r = discord.ui.TextInput(label="赤 (0-255)", placeholder="例: 255", required=True)
    g = discord.ui.TextInput(label="緑 (0-255)", placeholder="例: 0", required=True)
    b = discord.ui.TextInput(label="青 (0-255)", placeholder="例: 0", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            r_val = int(self.r.value)
            g_val = int(self.g.value)
            b_val = int(self.b.value)

            if not all(0 <= v <= 255 for v in [r_val, g_val, b_val]):
                raise ValueError("Out of range")

            color = discord.Color.from_rgb(r_val, g_val, b_val)
            hex_color = f"#{r_val:02X}{g_val:02X}{b_val:02X}"

            embed = discord.Embed(
                title="🎨 色のプレビュー",
                description=f"RGB: ({r_val}, {g_val}, {b_val})\nHex: `{hex_color}`",
                color=color
            )
            embed.set_footer(text="RGB Color Picker")

            class Buttons(discord.ui.View):
                def __init__(self, hexcolor: str, color: discord.Color, *, timeout = 180):
                    super().__init__(timeout=timeout)
                    self.color = color
                    self.hex = hexcolor

                @discord.ui.button(label="再度選択", style=discord.ButtonStyle.primary, emoji="🎨")
                async def reselect(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_modal(RGBModal())

                @discord.ui.button(label="ロール作成", style=discord.ButtonStyle.primary, emoji="➕")
                async def rolecreate(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.defer(ephemeral=True)
                    if not interaction.user.guild_permissions.manage_roles:
                        return await interaction.followup.send(content="権限がありません。", ephemeral=True)
                    role = await interaction.guild.create_role(name=f"{self.hex}-Color", color=self.color)
                    await interaction.followup.send(content=f"ロールを作成しました。\n{role.mention}", ephemeral=True)

            await interaction.response.send_message(embed=embed, view=Buttons(hex_color.replace("#", ""), color))
        except ValueError:
            await interaction.response.send_message("RGBの値は0〜255の整数で入力してください。", ephemeral=True)

class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> RoleCog")

    @commands.hybrid_group(name="role", description="ロールをメンバーに追加します。", fallback="add")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def role_add(self, ctx: commands.Context, メンバー: discord.Member, ロール: discord.Role):
        try:
            await ctx.defer()
            await メンバー.add_roles(ロール)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ロールを追加しました。", color=discord.Color.green(), description=f"{メンバー.mention}に{ロール.mention}を追加しました。"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="ロールを追加できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @role_add.command(name="remove", description="ロールをメンバーから削除します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_remove(self, ctx: commands.Context, メンバー: discord.Member, ロール: discord.Role):
        try:
            await ctx.defer()
            await メンバー.remove_roles(ロール)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ロールを削除しました。", color=discord.Color.green(), description=f"{メンバー.mention}から{ロール.mention}を削除しました。"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ロールを削除できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @role_add.command(name="create", description="ロールを作成します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_create(self, ctx: commands.Context, ロール名: str, 色: str):
        try:
            await ctx.defer()
            discord_color = discord.Colour(int(色[1:], 16))
            ロール = await ctx.guild.create_role(name=ロール名, color=discord_color)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ロールを作成しました。", color=discord.Color.green(), description=f"{ロール.mention}"))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ロールを作成できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ロールを作成できませんでした。", color=discord.Color.red(), description=f"```{e}```"))
        
    @role_add.command(name="color", description="カラーピッカーを使用します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_color(self, ctx: commands.Context):
        await ctx.interaction.response.send_modal(RGBModal())

    @role_add.command(name="info", description="ロール情報を取得します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_info(self, ctx: commands.Context, ロール: discord.Role):
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
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
            user_perms = [PERMISSION_TRANSLATIONS.get(perm, perm) for perm, value in ロール.permissions if value]
            user_perms_str = ", ".join(user_perms)
            await ctx.reply(embed=discord.Embed(title=f"<:Success:1362271281302601749> {ロール.name} の情報", color=discord.Color.blue()).add_field(name="ID", value=str(ロール.id), inline=False)
            .add_field(name="名前", value=str(ロール.name), inline=False).add_field(name="作成日時", value=str(ロール.created_at.astimezone(JST)), inline=False)
            .add_field(name="色", value=ロール.color.__str__(), inline=False)
            .add_field(name="権限", value=user_perms_str if user_perms_str != "" else "なし", inline=False)
            )
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ロールの情報を取得できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @role_add.command(name="oldusers-role", description="古参ロールを与えます。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def oldusers_role(self, ctx: commands.Context, 古参ロール: discord.Role):
        try:
            await ctx.defer()
            members_sorted = sorted(
                [m for m in ctx.guild.members if not m.bot], 
                key=lambda m: m.joined_at or ctx.message.created_at
            )
            kosan = members_sorted[:5]
            for k in kosan:
                await k.add_roles(古参ロール)
                await asyncio.sleep(1)
            await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 古参ロールを付与しました。", color=discord.Color.green(), description="\n".join([f"{kk.display_name} / {k.id}" for kk in kosan])))
        except discord.Forbidden as e:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> 古参ロールを付与できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        dbs = self.bot.async_db["Main"].MuteRoleSetting
        await dbs.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Role": role.id}, 
            upsert=True
        )

    async def get_mute_role(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].MuteRoleSetting
        try:
            data = await db.find_one({"Guild": ctx.guild.id}, {"_id": 0})
        except Exception as e:
            return None

        role_id = data.get("Role") if data else None
        if role_id is None:
            return None

        try:
            return await ctx.guild.fetch_role(role_id)
        except discord.NotFound:
            return None
        except discord.HTTPException:
            return None

    @role_add.command(name="mute", description="メンバーをミュートします。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_mute(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
        rl = await self.get_mute_role(ctx)
        if not rl:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ミュートロールがありません。", color=discord.Color.red(), description="先にミュートロールをセットアップしてください。"))
        await メンバー.add_roles(rl)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ミュートしました。", description=f"{メンバー.mention}", color=discord.Color.green()))

    @role_add.command(name="remove-mute", description="メンバーのミュートを解除します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_remove_mute(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
        rl = await self.get_mute_role(ctx)
        if not rl:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ミュートロールがありません。", color=discord.Color.red(), description="先にミュートロールをセットアップしてください。"))
        await メンバー.remove_roles(rl)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ミュートを解除しました。", description=f"{メンバー.mention}", color=discord.Color.green()))

    @role_add.command(name="sync-channel", description="ロールのチャンネルを同期します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def sync_channel(self, ctx: commands.Context):
        await ctx.defer()
        rl = await self.get_mute_role(ctx)
        if not rl:
            return await ctx.reply(embed=discord.Embed(title="<:Error:1362271424227709028> ミュートロールがありません。", color=discord.Color.red(), description="先にミュートロールをセットアップしてください。"))
        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(rl)
            changed = False

            if isinstance(channel, discord.TextChannel):
                if overwrite.send_messages != False:
                    overwrite.send_messages = False
                    changed = True
            elif isinstance(channel, discord.VoiceChannel):
                if overwrite.speak != False:
                    overwrite.speak = False
                    changed = True

            if changed:
                try:
                    await channel.set_permissions(rl, overwrite=overwrite)
                    await asyncio.sleep(1)
                except discord.Forbidden:
                    continue
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ロールのチャンネルを同期しました。", description=f"{rl.mention}", color=discord.Color.green()))

    @role_add.command(name="setting", description="ロールの設定を変更・確認します。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_setting(self, ctx: commands.Context):
        await ctx.defer()
        mute_rl = await self.get_mute_role(ctx)
        class RoleSetting(discord.ui.View):
            def __init__(self, author: discord.Member, set_mute_role):
                super().__init__(timeout=None)
                self.author = author
                self.set_mute_role = set_mute_role
                self.muted_role = None

            @discord.ui.select(
                cls=discord.ui.RoleSelect,
                placeholder="ロールを選択",
            )
            async def role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
                await interaction.response.defer(ephemeral=True)
                if not self.author.id == interaction.user.id:
                    return await interaction.followup.send("あなたのボタンではありません。", ephemeral=True)
                self.muted_role = select.values[0]
                return await interaction.followup.send(content=f"{select.values[0].mention}を選択しました。", ephemeral=True)

            @discord.ui.button(label="ミュートロールを設定", style=discord.ButtonStyle.gray)
            async def muterole_setting(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                if not self.author.id == interaction.user.id:
                    return await interaction.followup.send("あなたのボタンではありません。", ephemeral=True)
                if not self.muted_role:
                    return await interaction.followup.send("ロールが選択されていません。", ephemeral=True)
                await self.set_mute_role(ctx, self.muted_role)
                embed=discord.Embed(title="<:Success:1362271281302601749> ロールの設定", description=f"ミュートロール: {self.muted_role.mention}", color=discord.Color.green())
                await interaction.message.edit(embed=embed)
                return await interaction.followup.send("ミュートロールを設定しました。", ephemeral=True)

        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ロールの設定", description=f"ミュートロール: {mute_rl.mention if mute_rl else "未設定"}", color=discord.Color.green()), view=RoleSetting(ctx.author, self.set_mute_role))

    @role_add.command(name="setup", description="ロールをセットアップします。")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def role_setup(self, ctx: commands.Context):
        try:
            await ctx.reply("ロールをセットアップしています・・")
            muted = await ctx.guild.create_role(name="Muted-SharkBot")
            await self.set_mute_role(ctx, muted)
            for channel in ctx.guild.channels:
                overwrite = channel.overwrites_for(muted)
                changed = False

                if isinstance(channel, discord.TextChannel):
                    if overwrite.send_messages != False:
                        overwrite.send_messages = False
                        changed = True
                elif isinstance(channel, discord.VoiceChannel):
                    if overwrite.speak != False:
                        overwrite.speak = False
                        changed = True

                if changed:
                    try:
                        await channel.set_permissions(muted, overwrite=overwrite)
                    except discord.Forbidden:
                        continue
                await asyncio.sleep(1)
            await ctx.channel.send(embed=discord.Embed(title="<:Success:1362271281302601749> ロールをセットアップしました。", description=f"ミュートロール: {muted.mention}", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await ctx.channel.send(embed=discord.Embed(title="<:Error:1362271424227709028> ロールをセットアップできませんでした。", color=discord.Color.red(), description="権限エラーです。"))

async def setup(bot):
    await bot.add_cog(RoleCog(bot))