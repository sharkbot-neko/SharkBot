from discord.ext import commands
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
import socketio
import json

HOST = 'localhost'
PORT = 7000

class SocketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server = None
        self.server_task = None
        self.running = False

    async def start_socket_server(self):
        self.running = True
        self.server = await asyncio.start_server(
            self.handle_client, "localhost", 7000
        )
        print("[AsyncSocketCog] サーバー起動完了")

        self.server_task = asyncio.create_task(self.server.serve_forever())

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"[AsyncSocketCog] Connection from {addr}")

        try:
            while self.running:
                data = await reader.readline()
                if not data:
                    print(f"[AsyncSocketCog] Client {addr} disconnected")
                    break

                try:
                    received_json = json.loads(data.decode())
                    print(f"[AsyncSocketCog] Received JSON from {addr}: {received_json}")

                    if received_json.get("message") == "Test":
                        response = {
                            "status": "ok",
                            "message": "Testing OK!"
                        }
                    elif received_json.get("message") == "Test2":
                        response = {
                            "status": "ok",
                            "message": "Testing OK! - 2"
                        }
                    elif received_json.get("message") == "Guilds":
                        try:
                            user_id = int(received_json.get("User"))

                            guilds = self.bot.get_user(user_id).mutual_guilds

                            response = {
                                "status": "ok",
                                "message": [{"Name": g.name, "ID": g.id} for g in guilds]
                            }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "message": f"エラーが発生しました: {e}"
                            }
                    elif received_json.get("message") == "PermCheck":
                        try:
                            guild_id = int(received_json.get("Guild"))
                            user_id = int(received_json.get("User"))

                            guild = self.bot.get_guild(guild_id)
                            if guild is None:
                                response = {
                                    "status": "no",
                                    "perm": "no",
                                    "message": "そのサーバーにアクセスできません。"
                                }
                            else:
                                member = guild.get_member(user_id)
                                if member is None:
                                    response = {
                                        "status": "no",
                                        "perm": "no",
                                        "message": f"{guild.name} にそのユーザーはいません。"
                                    }
                                elif member.guild_permissions.administrator:
                                    response = {
                                        "status": "ok",
                                        "perm": "yes",
                                        "message": f"{guild.name} で管理者権限があります。"
                                    }
                                else:
                                    response = {
                                        "status": "no",
                                        "perm": "no",
                                        "message": f"{guild.name} で管理者権限がありません。"
                                    }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "perm": "no",
                                "message": f"エラーが発生しました: {e}"
                            }
                    elif received_json.get("message") == "Ban":
                        try:
                            guild_id = int(received_json.get("Guild"))
                            user_id = int(received_json.get("User"))

                            guild = self.bot.get_guild(guild_id)
                            if guild is None:
                                response = {
                                    "status": "no",
                                    "perm": "no",
                                    "message": "そのサーバーにアクセスできません。"
                                }
                            else:
                                member = guild.get_member(user_id)
                                if member is None:
                                    response = {
                                        "status": "no",
                                        "perm": "no",
                                        "message": f"{guild.name} にそのユーザーはいません。"
                                    }
                                elif member.guild_permissions.administrator:
                                    fet = await self.bot.fetch_user(int(received_json.get("BANUser")))
                                    try:
                                        await guild.ban(fet)
                                        response = {
                                            "status": "ok",
                                            "perm": "yes",
                                            "message": f"{guild.name} で管理者権限があったため、\n{fet.display_name} ({fet.id})をBANしました。"
                                        }
                                    except Exception as e:
                                        response = {
                                            "status": "error",
                                            "perm": "no",
                                            "message": f"エラーが発生しました: {e}"
                                        }
                                else:
                                    response = {
                                        "status": "no",
                                        "perm": "no",
                                        "message": f"{guild.name} で管理者権限がありません。"
                                    }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "perm": "no",
                                "message": f"エラーが発生しました: {e}"
                            }
                    else:
                        response = {
                            "status": "ok",
                            "received": received_json,
                            "message": "設定されている値以外が渡されました。"
                        }

                except json.JSONDecodeError:
                    response = {
                        "status": "error",
                        "message": "Invalid JSON received"
                    }
                    print(f"[AsyncSocketCog] Error: Invalid JSON from {addr}")

                writer.write(json.dumps(response).encode() + b"\n")
                await writer.drain()

        except Exception as e:
            print(f"[AsyncSocketCog] Unexpected error with {addr}: {e}")

        finally:
            writer.close()
            await writer.wait_closed()
            print(f"[AsyncSocketCog] Connection with {addr} closed")

    async def cog_load(self):
        await self.start_socket_server()

    async def cog_unload(self):
        print("[AsyncSocketCog] サーバー停止中")
        self.running = False
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        if self.server_task is not None:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            self.server_task = None
        print("[AsyncSocketCog] サーバー停止完了")

    @commands.command(name="check_flag")
    async def check_flag(self, ctx: commands.Context):
        if not ctx.author.id == 1335428061541437531:
            return
        await ctx.reply(f"{self.running}")

async def setup(bot):
    await bot.add_cog(SocketCog(bot))