import discord
from discord.ext import commands, tasks, ipc
import os
import asyncio
import logging
import sys
import json
from motor.motor_asyncio import AsyncIOMotorClient
import yaml
import sqlite3
import aiofiles
from pymongo import MongoClient

from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload

betacheck = sys.argv

intent = discord.Intents.default()
intent.members = True
intent.message_content = True

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

with open("../Token.json") as tk:
    tko = json.loads(tk.read())

class NewSharkBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self.ChangePrefix,
            help_command=None,
            intents=intent,
        )
        print("InitDone")
        self.ipc = Server(self, secret_key="🐼")
        self.async_db = AsyncIOMotorClient("mongodb://localhost:27017")
        self.sync_db = MongoClient("mongodb://localhost:27017")

    async def on_ipc_ready(self):
        print("Ipc server is ready.")

    async def on_ipc_error(self, endpoint, error):
        print(endpoint, "raised", error)

    def ChangePrefix(self, bot, message):
        pdb = self.sync_db["Main"].CustomPrefixBot
        if betacheck[1] == "nomal":
            try:
                dbfind = pdb.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return ["!.", "?."]
            if dbfind is None:
                return ["!.", "?."]
            return [dbfind["Prefix"], "!.", "?."]
        elif betacheck[1] == "beta":
            return "!!."
        else:
            return ["!.", "?."]
        
    async def share_func(self, ctx: commands.Context, word: str):
        await ctx.channel.send(embed=discord.Embed(title="共有先", description="チャンネルidを入力", color=discord.Color.yellow()))
        ms = await bot.wait_for("message", check=lambda ms: not ms.author.bot and ctx.author.id == ms.author.id, timeout=30)
        try:
            ch = await commands.TextChannelConverter().convert(ctx, ms.content)
            await ch.send(embed=discord.Embed(title=f"{ctx.author.name}からの共有", color=discord.Color.yellow(), description=f"{word}"))
            await ctx.channel.send(embed=discord.Embed(title="共有しました。", color=discord.Color.green()))
        except:
            await ctx.channel.send(embed=discord.Embed(title="共有に失敗しました。", color=discord.Color.red()))

    async def send_subcommand(self, ctx: commands.Context, catname: str):
        if ctx.invoked_subcommand is None:
            if len(catname.split(" ")) == 2:
                for i in bot.commands:
                    if i.name == catname.split(" ")[0]:
                        if type(i) == commands.Group:
                            for ic in i.commands:
                                if ic.name == catname.split(" ")[1]:
                                    if type(ic) == commands.Group:
                                        text = ""
                                        for c in ic.commands:
                                            if c.hidden:
                                                continue
                                            text += f"`{c.name}` {c.description}\n"
                                        await ctx.reply(embed=discord.Embed(title=f"`{ic.name}`のヘルプ", description=text, color=discord.Color.green()))
                                        return
                                    else:
                                        continue
            else:
                for i in bot.commands:
                    if i.name == catname:
                        if type(i) == commands.Group:
                            text = ""
                            for c in i.commands:
                                if c.hidden:
                                    continue
                                text += f"`{c.name}` {c.description}\n"
                            await ctx.reply(embed=discord.Embed(title=f"`{i.name}`のヘルプ", description=text, color=discord.Color.green()))
                            return
                        else:
                            continue

bot = NewSharkBot()

@bot.event
async def on_ready():
    await bot.load_extension('jishaku')
    if betacheck[1] == "nomal":
        await bot.change_presence(activity=discord.CustomActivity(name=f"{len(bot.guilds)}鯖 / {len(bot.users)}人  | /help"))
    elif betacheck[1] == "beta":
        await bot.change_presence(activity=discord.CustomActivity(name=f"{len(bot.guilds)}鯖 / {len(bot.users)}人  | !!.help"))
    loop_pres.start()
    os.system("cls")
    print("---[Logging]-------------------------------")
    print(f"BotName: {bot.user.name}")
    print("Ready.")
    await bot.get_channel(1349646266379927594).send(embed=discord.Embed(title="Botが起動しました。", color=discord.Color.green()).add_field(name="導入サーバー数", value=f"{len(bot.guilds)}サーバー"))

@tasks.loop(seconds=10)
async def loop_pres():
    if betacheck[1] == "nomal":
        await bot.change_presence(activity=discord.CustomActivity(name=f"{len(bot.guilds)}鯖 / {len(bot.users)}人 | /help"))
    elif betacheck[1] == "beta":
        await bot.change_presence(activity=discord.CustomActivity(name=f"{len(bot.guilds)}鯖 / {len(bot.users)}人 | !!.help"))

async def is_command_enabled(guild_id: int, command_name: str) -> bool:
    db = bot.async_db["Main"].CommandDisable
    settings = await db.find_one({"guild_id": guild_id})
    if not settings:
        return True
    try:
        disabled_commands = settings.get("disabled_commands", [])
        return command_name not in disabled_commands
    except:
        return True

@bot.event
async def on_message(message):
    return

@bot.event
async def setup_hook() -> None:
    if betacheck[1] == "nomal":
        for cog in os.listdir("cogs"):
            if cog.endswith(".py"):
                await bot.load_extension(f"cogs.{cog[:-3]}")
    elif betacheck[1] == "beta":
        for cog in os.listdir("test_cog"):
            if cog.endswith(".py"):
                await bot.load_extension(f"test_cog.{cog[:-3]}")
    await bot.tree.sync()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandNotFound):
        e = 0
        return e
    else:
        e = 0
        return e

if betacheck[1] == "nomal":
    bot.run(tko["Token"])
elif betacheck[1] == "beta":
    bot.run(tko["BetaToken"])
else:
    bot.run(tko["Token"])