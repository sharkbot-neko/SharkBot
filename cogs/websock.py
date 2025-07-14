from discord.ext import commands
import discord
import traceback
import sys
import logging
import json
import random
import time
import asyncio
import websockets
import re
from functools import partial
import time

class WockSocketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> WockSocketCog")
        self.ws_host = "localhost"
        self.ws_port = 7005
        self.websocket_server = None
        self.connected_clients = set()

    async def cog_load(self):
        self.websocket_server = asyncio.create_task(self.start_websocket_server())

    async def cog_unload(self):
        if self.websocket_server:
            self.websocket_server.cancel()
            await asyncio.gather(*(client.close() for client in self.connected_clients))
            self.connected_clients.clear()
            print("WebSocketサーバーが終了しました。")

    async def websocket_handler(self, websocket):
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("message") == "Test":
                    response_json = json.dumps({"message": "test"})
                    await websocket.send(response_json)
                elif data.get("message") == "Guilds":
                    try:
                        user_id = int(data.get("User"))
                        guilds = self.bot.get_user(user_id).mutual_guilds
                        response_json = json.dumps({"message": "Guilds", "data": [{"Name": g.name, "ID": g.id} for g in guilds]})
                        await websocket.send(response_json)
                    except:
                        response_json = json.dumps({"message": "Error"})
                        await websocket.send(response_json)
                        return 
                elif data.get("message") == "PermCheck":
                    try:
                        guild_id = int(data.get("Guild"))
                        user_id = int(data.get("User"))
                        guild = self.bot.get_guild(guild_id)
                        if guild is None:
                            response_json = json.dumps({"message": "Error", "Data": "アクセス権限がありません。"})
                            await websocket.send(response_json)
                        else:
                            member = guild.get_member(user_id)
                            if not member:
                                response_json = json.dumps({"message": "Error", "Data": "そのサーバーにいません。"})
                                await websocket.send(response_json)
                            elif member.guild_permissions.administrator:
                                response_json = json.dumps({"message": "PermCheck", "Data": f"{guild.name} で権限があります。"})
                                await websocket.send(response_json)
                            else:
                                response_json = json.dumps({"message": "PermCheck", "Data": f"{guild.name} で権限がありません。"})
                                await websocket.send(response_json)
                    except Exception as e:
                        response_json = json.dumps({"message": "Error", "Data": f"予期しないエラーが発生しました。"})
                        await websocket.send(response_json)
                elif data.get("message") == "Ban":
                    try:
                        guild_id = int(data.get("Guild"))
                        user_id = int(data.get("User"))
                        guild = self.bot.get_guild(guild_id)
                        if guild is None:
                            response_json = json.dumps({"message": "Error", "Data": "アクセス権限がありません。"})
                            await websocket.send(response_json)
                        else:
                            member = guild.get_member(user_id)
                            if not member:
                                response_json = json.dumps({"message": "Error", "Data": "そのサーバーにいません。"})
                                await websocket.send(response_json)
                            elif member.guild_permissions.administrator:
                                try:
                                    fet = await self.bot.fetch_user(int(data.get("BANUser")))
                                    await guild.ban(fet)
                                    response_json = json.dumps({"message": "BAN", "Data": f"{guild.name} で{fet.display_name}のBANを実行しました。"})
                                    await websocket.send(response_json)
                                except:
                                    response_json = json.dumps({"message": "Error", "Data": f"{guild.name} でBotの権限がありません。"})
                                    await websocket.send(response_json)
                            else:
                                response_json = json.dumps({"message": "Error", "Data": f"{guild.name} で権限がありません。"})
                                await websocket.send(response_json)
                    except Exception as e:
                        response_json = json.dumps({"message": "Error", "Data": f"予期しないエラーが発生しました。"})
                        await websocket.send(response_json)
        except websockets.ConnectionClosedError:
            print(f"{self.__class__.__name__}: WebSocketクライアントが切断しました。")
        except json.JSONDecodeError:
            print(f"{self.__class__.__name__}: WebSocketクライアントが切断しました。")
        finally:
            self.connected_clients.remove(websocket)

    async def start_websocket_server(self):
        async with websockets.serve(self.websocket_handler, self.ws_host, self.ws_port):
            print(f"{self.__class__.__name__}: WebSocketサーバーが ws://{self.ws_host}:{self.ws_port} で起動しました。")
            await asyncio.Future()

    async def broadcast_message(self, message: str):
        if self.connected_clients:
            print(f"{self.__class__.__name__}: ブロードキャスト: {message}")
            await asyncio.gather(*(client.send(message) for client in self.connected_clients))

async def setup(bot):
    await bot.add_cog(WockSocketCog(bot))