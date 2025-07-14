from discord.ext import commands
import discord
import traceback
import sys
import logging
import time
import asyncio

COOLDOWN_TIME = 15
user_last_message_time = {}

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

class LockMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LockMessageCog")

    async def add_reaction_lockmsg(self, message: discord.Message):
        db = self.bot.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            await discord.PartialMessage(channel=message.channel, id=dbfind["MessageID"]).add_reaction("🔄")
        except:
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if '!.' in message.content:
            return
        user_id = message.author.id
        db = self.bot.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = user_last_message_time.get(user_id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time[user_id] = current_time
        await self.add_reaction_lockmsg(message)
        await asyncio.sleep(5)
        try:
            await discord.PartialMessage(channel=message.channel, id=dbfind["MessageID"]).delete()
        except:
            pass
        await asyncio.sleep(2)
        msg = await message.channel.send(embed=discord.Embed(title=dbfind["Title"], description=dbfind["Desc"], color=discord.Color.random()), view=LockMessageRemove())
        await db.replace_one(
            {"Channel": message.channel.id, "Guild": message.guild.id}, 
            {"Channel": message.channel.id, "Guild": message.guild.id, "Title": dbfind["Title"], "Desc": dbfind["Desc"], "MessageID": msg.id}, 
            upsert=True
        )

async def setup(bot):
    await bot.add_cog(LockMessageCog(bot))