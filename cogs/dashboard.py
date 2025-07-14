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

class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> DashboardCog")
        self.ws_host = "localhost"
        self.ws_port = 7006
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
    await bot.add_cog(DashboardCog(bot))