from discord.ext import commands
from discord import app_commands
from urllib.parse import quote
import discord
import traceback
import sys
import logging
from collections import Counter
from urllib.parse import urlparse
import neologdn
import pyshorteners
import time
import aiofiles
import datetime
import random, string
import asyncio
import aiohttp
import json
from functools import partial
import re
import urllib
from urllib.parse import urlparse, parse_qs
import MeCab
import requests
from bs4 import BeautifulSoup
import urllib.parse
import io
import base64
import mimetypes
from werkzeug.utils import secure_filename
import socket
import dns.asyncresolver
import os
import uuid

def UploadFile(io, filename: str):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://firestorage.jp/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'act': 'flashupjs',
        'type': 'flash10b',
        'photo': '1',
        'talk': '1',
        'json': '1',
        'eid': '',
    }

    uploadfolder = requests.get('https://firestorage.jp/flashup.cgi', params=params, headers=headers)

    uploadid = uploadfolder.json()

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Origin': 'https://firestorage.jp',
        'Referer': 'https://firestorage.jp/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    mime_type, _ = mimetypes.guess_type(filename)

    files = [
            ('folder_id', (None, f'{uploadid["folder_id"]}')),
            ('ppass', (None, '')),
            ('dpass', (None, '')),
            ('thumbnail', (None, 'nomal')),
            ('top', (None, '1')),
            ('jqueryupload', (None, '1')),
            ('max_size', (None, '2147483648')),
            ('max_sized', (None, '2')),
            ('max_size_photo', (None, '15728640')),
            ('max_size_photod', (None, '15')),
            ('max_size_photo', (None, '150')),
            ('max_count', (None, '20')),
            ('max_count_photo', (None, '150')),
            ('jqueryupload', (None, '1')),
            ('eid', (None, '')),
            ('processid', (None, f'{uploadid["folder_id"]}')),
            ('qst', (None, 'n1=Mozilla&n2=Netscape&n3=Win32&n4=Mozilla/5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit/537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome/131.0.0.0%20Safari/537.36')),
            ('comments', (None, '')),
            ('comment', (None, '')),
            ('arc', (None, '')),
            ('zips', (None, '')),
            ('file_queue', (None, '1')),
            ('pc', (None, '1')),
            ('exp', (None, '7')),
            ('Filename', (f"{filename}", io, mime_type)),
    ]

    response = requests.post('https://server73.firestorage.jp/upload.cgi', headers=headers, files=files)

    decoded_str = urllib.parse.unquote(response.text)

    soup = BeautifulSoup(decoded_str, 'html.parser')

    download_url = soup.find('a', {'id': 'downloadlink'})['href']

    return download_url

COOLDOWN_TIME = 5
user_last_message_time = {}

class RunPython(discord.ui.Modal, title='Pythonを実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='print(1+1)',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/python',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        
        json_data = {
            'name': 'Python',
            'title': 'Python Hello World',
            'version': '3.6',
            'mode': 'python',
            'description': None,
            'extension': 'py',
            'concurrentJobs': 10,
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'python',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'main.py',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New Python file',
                        'name': 'script${i}.py',
                        'content': '# In main file\n# import script${i}\n# print(script${i}.sum(1, 3))\n\ndef sum(a, b):\n    return a + b',
                    },
                ],
            },
            'visibility': 'public',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="Pythonの実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。\nWhileなどは使用できません。')

class RunNodeJS(discord.ui.Modal, title='NodoJSを実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='console.log(1+1);',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/nodejs',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'NodeJS',
            'title': 'NodeJS Hello World',
            'version': '12.13',
            'mode': 'javascript',
            'description': None,
            'extension': 'js',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'nodejs',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'index.js',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New JS file',
                        'name': 'script${i}.js',
                        'content': "/**\n *  In main file\n *  let script${i} = require('./script${i}');\n *  console.log(script${i}.sum(1, 2));\n */\n\nfunction sum(a, b) {\n    return a + b;\n}\n\nmodule.exports = { sum };",
                    },
                    {
                        'helpText': 'Add Dependencies',
                        'name': 'package.json',
                        'content': '{\n  "name": "main_app",\n  "version": "1.0.0",\n  "description": "",\n  "main": "HelloWorld.js",\n  "dependencies": {\n    "lodash": "^4.17.21"\n  }\n}',
                    },
                ],
            },
            'visibility': 'public',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="Nodejsの実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。')

class RunCPlapla(discord.ui.Modal, title='C++を実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='printf("aaa")',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/cpp',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'C++',
            'title': 'C++ Hello World',
            'version': 'latest',
            'mode': 'c_cpp',
            'description': None,
            'extension': 'cpp',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'cpp',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'Main.cpp',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New C++ file',
                        'name': 'NewFile${i}.cpp',
                        'content': '#include <iostream>\n\n// Follow the steps below to use this file\n\n// 1. In main file add the following include \n// #include "NewFile${i}.cpp"\n\n// 2. Add the following in the code\n// sayHelloFromNewFile${i}();\n\nvoid sayHelloFromNewFile${i}() {\n    std::cout << "\\nHello from New File ${i}!\\n";\n}\n',
                    },
                    {
                        'helpText': 'New Text file',
                        'name': 'sample${i}.txt',
                        'content': 'Sample text file!',
                    },
                ],
            },
            'visibility': 'public',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="C++の実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send(f'エラー。\n{sys.exc_info()}')

class RunCSharp(discord.ui.Modal, title='C#を実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='Console.WriteLine("Hello world!");',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/csharp',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'C#',
            'title': 'C# Hello World!',
            'mode': 'csharp',
            'description': None,
            'extension': 'cs',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'csharp',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'HelloWorld.cs',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New C# file',
                        'name': 'NewClass${i}.cs',
                        'content': 'using System;\n\nnamespace HelloWorld\n{\n\tpublic class NewClass${i}\n\t{\n\t\t// Follow the steps below to use this file\n\n\t\t// 1. In the main file (e.g., HelloWorld.cs), create an instance of this class:\n\t\t// NewClass${i} instance${i} = new NewClass${i}();\n\n\t\t// 2. Call the method to get the greeting message:\n\t\t// Console.WriteLine(instance${i}.SayHelloFromNewClass());\n\n\t\tpublic string SayHelloFromNewClass()\n\t\t{\n\t\t\treturn "Hello from New Class ${i}!";\n\t\t}\n\t}\n}',
                    },
                ],
            },
            'visibility': 'public',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="C#の実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。')

class RunEmbedMake(discord.ui.Modal, title='埋め込みを作成'):
    title_ = discord.ui.TextInput(
        label='タイトル',
        placeholder='タイトル！',
        style=discord.TextStyle.short,
    )

    desc = discord.ui.TextInput(
        label='説明',
        placeholder='説明！',
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label='色',
        placeholder='#000000',
        style=discord.TextStyle.short,
        default="#000000"
    )

    button_label = discord.ui.TextInput(
        label='ボタンラベル',
        placeholder='Webサイト',
        style=discord.TextStyle.short,
        required=False
    )

    button = discord.ui.TextInput(
        label='ボタンurl',
        placeholder='https://www.sharkbot.xyz/',
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        banned_words = ['児童', 'sex', 'anal', 'ポルノ', 'エロ', 'セックス', 'ちんこ', 'まんこ', '殺す', '死ね', 'バカ', '吃', '唖', '妾', '嬢', '盲', '聾', '跛', '躄', 'アカ', 'イモ', 'ガキ', 'ガサ', 'キチ', 'キ印', 'クロ', 'サツ', 'シマ', 'スケ', 'チビ', 'デカ', 'ドヤ', 'ノビ', 'ヒモ', 'ブス', 'ブツ', 'ヨツ', '丁稚', '三助', '下女', '下男', '不具', '中共', '乞食', '二号', '人夫', '人足', '令嬢', '低脳', '保母', '傴僂', '北鮮', '南鮮', '土人', '土工', '土方', '坊主', '坑夫', '外人', '女中', '女傑', '女工', '女給', '姦通', '子供', '家柄', '家系', '寄目', '小人', '小僧', '屑屋', '屠殺', '工夫', '床屋', '強姦', '情夫', '情婦', '愚鈍', '按摩', '支那', '文盲', '明盲', '板前', '業病', '正妻', '毛唐', '淫売', '満州', '漁夫', '父兄', '片目', '片端', '片肺', '片親', '片足', '狂う', '狂人', '狂女', '狂気', '猫糞', '獣医', '産婆', '田舎', '番太', '癩病', '白痴', '百姓', '盲人', '盲目', '盲縞', '移民', '穢多', '端女', '精薄', '給仕', '老婆', '職工', '肌色', '色盲', '芸人', '苦力', '虚仮', '血筋', '血統', '親方', '貧農', '身分', '農夫', '近目', '部落', '酋長', '醜男', '鉱夫', '隠坊', '露助', '青姦', '非人', '飯場', '養護', '馬丁', '馬喰', '魚屋', '鮮人', '黒人', 'ＯＬ', 'うんこ', 'お巡り', 'アメ公', 'アル中', 'イタ公', 'オカマ', 'カッペ', 'クンニ', 'コロシ', 'ゴミ屋', 'サラ金', 'ザギン', 'ジャリ', 'ジュー', 'スラム', 'タタキ', 'チョン', 'ドヤ街', 'ナオン', 'ニガー', 'ニグロ', 'ハーフ', 'バタ屋', 'パクる', 'パン助', 'ブタ箱', 'ペイ中', 'ペイ患', 'ポリ公', 'マンコ', 'ヤバい', 'ヤー様', '三つ口', '三国人', '人非人', '代書屋', '低脳児', '借り腹', '八百屋', '共稼ぎ', '処女作', '処女峰', '出戻り', '出稼ぎ', '助産婦', '労務者', '千摺り', '半島人', '名門校', '周旋屋', '四つ足', '四つ辻', '土建屋', '地回り', '女子供', '孤児院', '寄せ場', '小使い', '尻拭い', '屠殺人', '屠殺場', '当て馬', '役不足', '後進国', '心障児', '心障者', '手ん棒', '担ぎ屋', '拡張員', '拡張団', '掃除夫', '掃除婦', '支那人', '支那竹', '新平民', '日雇い', '未亡人', '未開人', '気違い', '沖仲仕', '浮浪児', '浮浪者', '潜水夫', '犬殺し', '町医者', '痴呆症', '皮切り', '皮被り', '盲滅法', '看護婦', '確信犯', '第三国', '紅毛人', '聾桟敷', '脳膜炎', '興信所', '蒙古症', '藪医者', '藪睨み', '蛸部屋', '表日本', '裏日本', '足切り', '踏切番', '連れ子', '過去帳', '郵便夫', '郵便屋', '障害者', '雑役夫', '養老院', '首切り', '黒んぼ', 'あらめん', 'おわい屋', 'かったい', 'がちゃ目', 'ぎっちょ', 'しらっこ', 'ずらかる', 'どさ回り', 'どん百姓', 'ほんぼし', 'ぽん引き', 'まえつき', 'めっかち', 'やさぐれ', 'アイヌ系', 'イカサマ', 'インチキ', 'ゲンナマ', 'ゲーセン', 'ジプシー', 'ジャップ', 'トルコ嬢', 'ニコヨン', 'パーマ屋', 'ポコペン', 'ヤンキー', 'ルンペン', 'ロンパリ', '三韓征伐', '不可触民', '不治の病', '他力本願', '伊勢乞食', '低開発国', '保線工夫', '台湾ハゲ', '台湾政府', '合いの子', '土左衛門', '垂れ流す', '士農工商', '婿をとる', '嫁にやる', '川向こう', '引かれ者', '拡張団長', '支那料理', '支那蕎麦', '朝鮮人参', '朝鮮征伐', '未開発国', '植物人間', '河原乞食', '溺れ死ぬ', '滑り止め', '片手落ち', '特殊学校', '特殊学級', '特殊部落', '発狂する', '盲愛する', '知恵遅れ', '精神異常', '線路工夫', '自閉症児', '落とし前', '落人部落', '足を洗う', '身元調査', '運ちゃん', '釣り書き', '魔女っ子', 'いちゃもん', 'かさっかき', 'くわえ込む', 'すけこまし', 'エスキモー', 'エディター', 'ズージャー', 'ダッチマン', 'チャリンコ', 'チャンコロ', 'トルコ風呂', 'ポッポー屋', '上方の贅六', '富山の三助', '気違い沙汰', '汲み取り屋', '灸を据える', '狂気の沙汰', '玉袋筋太郎', '盲判を押す', '精神分裂病', '股に掛ける', '育ちより氏', '落ちこぼれ', '蛙の子は蛙', 'がっぷり四つ', 'オールドミス', 'サラブレッド', 'タケノコ医者', '娘を片付ける', '本腰を入れる', '気違いに刃物', '盲蛇に怖じず', '越後の米つき', 'エチゼンクラゲ', 'スチュワーデス', 'レントゲン技師', '将棋倒しになる', '日本のチベット', '群盲象をなでる', 'ブラインドタッチ', '女の腐ったような', '馬鹿チョンカメラ', '南部の鮭の鼻まがり', '天才と狂人は紙一重', '馬鹿でもチョンでも', 'インディアン嘘つかない', '健全なる精神は健全なる身体に宿る', 'NTR', 'NㄒR', 'Tバック', 'えっち', 'えっㄎ', 'えっㄘ', 'おちんちん', 'おㄎんㄎん', 'おㄘんㄘん', 'さかさ椋鳥', 'せきれい本手', 'せっくす', 'せっㄑす', 'だいしゅきホールド', 'だいしゅきホーㄦド', 'ちんこ', 'ちんちん', 'ちんぽ', 'ひとりえっち', 'ひとりえっㄎ', 'ひとりえっㄘ', 'アクメ', 'アクㄨ', 'アダルトビデオ', 'アダㄦトビデオ', 'アナル', 'アナルセックス', 'アナルビーズ', 'アナルプラグ', 'アナル拡張', 'アナル開発', 'アナルＳＥＸ', 'アナㄦ', 'アナㄦセックス', 'アナㄦビーズ', 'アナㄦプラグ', 'アナㄦ拡張', 'アナㄦ開発', 'アナㄦＳＥＸ', 'イメクラ', 'イメージビデオ', 'イㄨクラ', 'イㄨージビデオ', 'エクスタシー', 'エッチ', 'エロ', 'エロい', 'エロ同人', 'エロ同人誌', 'エロ本', 'オナホール', 'オナホーㄦ', 'オーガズム', 'オーガズㄊ', 'オーガズㄙ', 'カウパー', 'カントン包茎', 'ギャグボール', 'ギャグボーㄦ', 'コンドーム', 'コンドーㄊ', 'コンドーㄙ', 'ザーメン', 'ザーㄨン', 'スカトロ', 'スペルマ', 'スペㄦマ', 'スㄌトロ', 'ダブルピース', 'ダブㄦピース', 'ディルド', 'ディㄦド', 'デカチン', 'デリバリーヘルス', 'デリバリーヘㄦス', 'デリヘル', 'デリヘㄦ', 'デㄌチン', 'ハメ撮り', 'ハーレム', 'ハーレㄊ', 'ハーレㄙ', 'ハㄨ撮り', 'バキュームフェラ', 'バキューㄊフェラ', 'バキューㄙフェラ', 'ブルセラ', 'ブㄦセラ', 'ポルチオ', 'ポㄦチオ', 'ムラムラ', 'ラブドール', 'ラブドーㄦ', 'ラブホテル', 'ラブホテㄦ', 'ㄊラㄊラ', 'ㄌウパー', 'ㄌントン包茎', 'ㄎんこ', 'ㄎんぽ', 'ㄎんㄎん', 'ㄒバック', 'ㄘんこ', 'ㄘんぽ', 'ㄘんㄘん', 'ㄙラㄙラ', 'ㄛかㄛ椋鳥', 'ㄜかㄜ椋鳥', 'ㄝきれい本手', 'ㄝっくす', 'ㄝっㄑす', 'ㆥきれい本手', 'ㆥっくす', 'ㆥっㄑす', 'ㆲクスタシー', 'ㆲッチ', 'ㆲロ', 'ㆲロい', 'ㆲロ同人', 'ㆲロ同人誌', 'ㆲロ本', '兜合わせ', '兜合わㄝ', '兜合わㆥ', '孕ませ', '孕まㄝ', '孕まㆥ', '快楽堕ち', '快楽堕ㄎ', '快楽堕ㄘ', '朝勃ち', '朝勃ㄎ', '朝勃ㄘ', '朝起ち', '朝起ㄎ', '朝起ㄘ', '生ハメ', '生ハㄨ', '立ちんぼ', '立ㄎんぼ', '立ㄘんぼ', '筆おろし', '筆おㄋし', '貝合わせ', '貝合わㄝ', '貝合わㆥ', '逆アナル', '逆アナㄦ', '黒ギャル', '黒ギャㄦ']
        banned_words2 = ['3O', '3X', '3o', '3x', '3■', '3□', '3○', '3◯', '3⚪', '3✗', 'AO女O', 'AX女X', 'Ao女o', 'Ax女x', 'A■女■', 'A□女□', 'A○女○', 'A◯女◯', 'A⚪女⚪', 'A✗女✗', 'GOポOト', 'GXポXト', 'Goポoト', 'Gxポxト', 'G■ポ■ト', 'G□ポ□ト', 'G○ポ○ト', 'G◯ポ◯ト', 'G⚪ポ⚪ト', 'G✗ポ✗ト', 'NOR', 'NXR', 'NoR', 'NxR', 'N■R', 'N□R', 'N○R', 'N◯R', 'N⚪R', 'N✗R', 'SO', 'SOD', 'SOX', 'SX', 'SXD', 'SXX', 'So', 'SoD', 'SoX', 'Sx', 'SxD', 'SxX', 'S■', 'S■D', 'S■X', 'S□', 'S□D', 'S□X', 'S○', 'S○D', 'S○X', 'S◯', 'S◯D', 'S◯X', 'S⚪', 'S⚪D', 'S⚪X', 'S✗', 'S✗D', 'S✗X', 'TOッO', 'TXッX', 'Toッo', 'Txッx', 'T■ッ■', 'T□ッ□', 'T○ッ○', 'T◯ッ◯', 'T⚪ッ⚪', 'T✗ッ✗', 'いOらOい', 'いXらXい', 'いoらoい', 'いxらxい', 'い■ら■い', 'い□ら□い', 'い○ら○い', 'い◯ら◯い', 'い⚪ら⚪い', 'い✗ら✗い', 'えOち', 'えXち', 'えoち', 'えxち', 'え■ち', 'え□ち', 'え○ち', 'え◯ち', 'え⚪ち', 'え✗ち', 'おOπ', 'おOこ', 'おOにO', 'おOぱO', 'おOんO', 'おOんOん', 'おOシOタ', 'おO除OェO', 'おXπ', 'おXこ', 'おXにX', 'おXぱX', 'おXんX', 'おXんXん', 'おXシXタ', 'おX除XェX', 'おoπ', 'おoこ', 'おoにo', 'おoぱo', 'おoんo', 'おoんoん', 'おoシoタ', 'おo除oェo', 'おxπ', 'おxこ', 'おxにx', 'おxぱx', 'おxんx', 'おxんxん', 'おxシxタ', 'おx除xェx', 'お■π', 'お■こ', 'お■に■', 'お■ぱ■', 'お■ん■', 'お■ん■ん', 'お■シ■タ', 'お■除■ェ■', 'お□π', 'お□こ', 'お□に□', 'お□ぱ□', 'お□ん□', 'お□ん□ん', 'お□シ□タ', 'お□除□ェ□', 'お○π', 'お○こ', 'お○に○', 'お○ぱ○', 'お○ん○', 'お○ん○ん', 'お○シ○タ', 'お○除○ェ○', 'お◯π', 'お◯こ', 'お◯に◯', 'お◯ぱ◯', 'お◯ん◯', 'お◯ん◯ん', 'お◯シ◯タ', 'お◯除◯ェ◯', 'お⚪π', 'お⚪こ', 'お⚪に⚪', 'お⚪ぱ⚪', 'お⚪ん⚪', 'お⚪ん⚪ん', 'お⚪シ⚪タ', 'お⚪除⚪ェ⚪', 'お✗π', 'お✗こ', 'お✗に✗', 'お✗ぱ✗', 'お✗ん✗', 'お✗ん✗ん', 'お✗シ✗タ', 'お✗除✗ェ✗', 'きOたO', 'きXたX', 'きoたo', 'きxたx', 'き■た■', 'き□た□', 'き○た○', 'き◯た◯', 'き⚪た⚪', 'き✗た✗', 'さOさO鳥', 'さXさX鳥', 'さoさo鳥', 'さxさx鳥', 'さ■さ■鳥', 'さ□さ□鳥', 'さ○さ○鳥', 'さ◯さ◯鳥', 'さ⚪さ⚪鳥', 'さ✗さ✗鳥', 'しOりO蓉', 'しXりX蓉', 'しoりo蓉', 'しxりx蓉', 'し■り■蓉', 'し□り□蓉', 'し○り○蓉', 'し◯り◯蓉', 'し⚪り⚪蓉', 'し✗り✗蓉', 'すOべ', 'すXべ', 'すoべ', 'すxべ', 'す■べ', 'す□べ', 'す○べ', 'す◯べ', 'す⚪べ', 'す✗べ', 'せOくO', 'せOれO本O', 'せXくX', 'せXれX本X', 'せoくo', 'せoれo本o', 'せxくx', 'せxれx本x', 'せ■く■', 'せ■れ■本■', 'せ□く□', 'せ□れ□本□', 'せ○く○', 'せ○れ○本○', 'せ◯く◯', 'せ◯れ◯本◯', 'せ⚪く⚪', 'せ⚪れ⚪本⚪', 'せ✗く✗', 'せ✗れ✗本✗', 'だOしOきOーOド', 'だXしXきXーXド', 'だoしoきoーoド', 'だxしxきxーxド', 'だ■し■き■ー■ド', 'だ□し□き□ー□ド', 'だ○し○き○ー○ド', 'だ◯し◯き◯ー◯ド', 'だ⚪し⚪き⚪ー⚪ド', 'だ✗し✗き✗ー✗ド', 'ちOこ', 'ちOちO', 'ちOぽ', 'ちXこ', 'ちXちX', 'ちXぽ', 'ちoこ', 'ちoちo', 'ちoぽ', 'ちxこ', 'ちxちx', 'ちxぽ', 'ち■こ', 'ち■ち■', 'ち■ぽ', 'ち□こ', 'ち□ち□', 'ち□ぽ', 'ち○こ', 'ち○ち○', 'ち○ぽ', 'ち◯こ', 'ち◯ち◯', 'ち◯ぽ', 'ち⚪こ', 'ち⚪ち⚪', 'ち⚪ぽ', 'ち✗こ', 'ち✗ち✗', 'ち✗ぽ', 'ひOりOっO', 'ひXりXっX', 'ひoりoっo', 'ひxりxっx', 'ひ■り■っ■', 'ひ□り□っ□', 'ひ○り○っ○', 'ひ◯り◯っ◯', 'ひ⚪り⚪っ⚪', 'ひ✗り✗っ✗', 'ふOなO', 'ふXなX', 'ふoなo', 'ふxなx', 'ふ■な■', 'ふ□な□', 'ふ○な○', 'ふ◯な◯', 'ふ⚪な⚪', 'ふ✗な✗', 'まOぐO返O', 'まOこ', 'まOまO', 'まXぐX返X', 'まXこ', 'まXまX', 'まoぐo返o', 'まoこ', 'まoまo', 'まxぐx返x', 'まxこ', 'まxまx', 'ま■ぐ■返■', 'ま■こ', 'ま■ま■', 'ま□ぐ□返□', 'ま□こ', 'ま□ま□', 'ま○ぐ○返○', 'ま○こ', 'ま○ま○', 'ま◯ぐ◯返◯', 'ま◯こ', 'ま◯ま◯', 'ま⚪ぐ⚪返⚪', 'ま⚪こ', 'ま⚪ま⚪', 'ま✗ぐ✗返✗', 'ま✗こ', 'ま✗ま✗', 'むOむO', 'むXむX', 'むoむo', 'むxむx', 'む■む■', 'む□む□', 'む○む○', 'む◯む◯', 'む⚪む⚪', 'む✗む✗', 'アOニO', 'アOマO', 'アOメ', 'アOル', 'アOルOッOス', 'アOルOビOオ', 'アOルOラO', 'アOルOーO', 'アOルO張', 'アOルO発', 'アOルOＥO', 'アO顔', 'アXニX', 'アXマX', 'アXメ', 'アXル', 'アXルXッXス', 'アXルXビXオ', 'アXルXラX', 'アXルXーX', 'アXルX張', 'アXルX発', 'アXルXＥX', 'アX顔', 'アoニo', 'アoマo', 'アoメ', 'アoル', 'アoルoッoス', 'アoルoビoオ', 'アoルoラo', 'アoルoーo', 'アoルo張', 'アoルo発', 'アoルoＥo', 'アo顔', 'アxニx', 'アxマx', 'アxメ', 'アxル', 'アxルxッxス', 'アxルxビxオ', 'アxルxラx', 'アxルxーx', 'アxルx張', 'アxルx発', 'アxルxＥx', 'アx顔', 'ア■ニ■', 'ア■マ■', 'ア■メ', 'ア■ル', 'ア■ル■ッ■ス', 'ア■ル■ビ■オ', 'ア■ル■ラ■', 'ア■ル■ー■', 'ア■ル■張', 'ア■ル■発', 'ア■ル■Ｅ■', 'ア■顔', 'ア□ニ□', 'ア□マ□', 'ア□メ', 'ア□ル', 'ア□ル□ッ□ス', 'ア□ル□ビ□オ', 'ア□ル□ラ□', 'ア□ル□ー□', 'ア□ル□張', 'ア□ル□発', 'ア□ル□Ｅ□', 'ア□顔', 'ア○ニ○', 'ア○マ○', 'ア○メ', 'ア○ル', 'ア○ル○ッ○ス', 'ア○ル○ビ○オ', 'ア○ル○ラ○', 'ア○ル○ー○', 'ア○ル○張', 'ア○ル○発', 'ア○ル○Ｅ○', 'ア○顔', 'ア◯ニ◯', 'ア◯マ◯', 'ア◯メ', 'ア◯ル', 'ア◯ル◯ッ◯ス', 'ア◯ル◯ビ◯オ', 'ア◯ル◯ラ◯', 'ア◯ル◯ー◯', 'ア◯ル◯張', 'ア◯ル◯発', 'ア◯ル◯Ｅ◯', 'ア◯顔', 'ア⚪ニ⚪', 'ア⚪マ⚪', 'ア⚪メ', 'ア⚪ル', 'ア⚪ル⚪ッ⚪ス', 'ア⚪ル⚪ビ⚪オ', 'ア⚪ル⚪ラ⚪', 'ア⚪ル⚪ー⚪', 'ア⚪ル⚪張', 'ア⚪ル⚪発', 'ア⚪ル⚪Ｅ⚪', 'ア⚪顔', 'ア✗ニ✗', 'ア✗マ✗', 'ア✗メ', 'ア✗ル', 'ア✗ル✗ッ✗ス', 'ア✗ル✗ビ✗オ', 'ア✗ル✗ラ✗', 'ア✗ル✗ー✗', 'ア✗ル✗張', 'ア✗ル✗発', 'ア✗ル✗Ｅ✗', 'ア✗顔', 'イO', 'イOクO', 'イOポ', 'イOポOンO', 'イOマOオ', 'イOモO', 'イOャOチOセOクO', 'イOャOブOッOス', 'イOーOビOオ', 'イX', 'イXクX', 'イXポ', 'イXポXンX', 'イXマXオ', 'イXモX', 'イXャXチXセXクX', 'イXャXブXッXス', 'イXーXビXオ', 'イo', 'イoクo', 'イoポ', 'イoポoンo', 'イoマoオ', 'イoモo', 'イoャoチoセoクo', 'イoャoブoッoス', 'イoーoビoオ', 'イx', 'イxクx', 'イxポ', 'イxポxンx', 'イxマxオ', 'イxモx', 'イxャxチxセxクx', 'イxャxブxッxス', 'イxーxビxオ', 'イ■', 'イ■ク■', 'イ■ポ', 'イ■ポ■ン■', 'イ■マ■オ', 'イ■モ■', 'イ■ャ■チ■セ■ク■', 'イ■ャ■ブ■ッ■ス', 'イ■ー■ビ■オ', 'イ□', 'イ□ク□', 'イ□ポ', 'イ□ポ□ン□', 'イ□マ□オ', 'イ□モ□', 'イ□ャ□チ□セ□ク□', 'イ□ャ□ブ□ッ□ス', 'イ□ー□ビ□オ', 'イ○', 'イ○ク○', 'イ○ポ', 'イ○ポ○ン○', 'イ○マ○オ', 'イ○モ○', 'イ○ャ○チ○セ○ク○', 'イ○ャ○ブ○ッ○ス', 'イ○ー○ビ○オ', 'イ◯', 'イ◯ク◯', 'イ◯ポ', 'イ◯ポ◯ン◯', 'イ◯マ◯オ', 'イ◯モ◯', 'イ◯ャ◯チ◯セ◯ク◯', 'イ◯ャ◯ブ◯ッ◯ス', 'イ◯ー◯ビ◯オ', 'イ⚪', 'イ⚪ク⚪', 'イ⚪ポ', 'イ⚪ポ⚪ン⚪', 'イ⚪マ⚪オ', 'イ⚪モ⚪', 'イ⚪ャ⚪チ⚪セ⚪ク⚪', 'イ⚪ャ⚪ブ⚪ッ⚪ス', 'イ⚪ー⚪ビ⚪オ', 'イ✗', 'イ✗ク✗', 'イ✗ポ', 'イ✗ポ✗ン✗', 'イ✗マ✗オ', 'イ✗モ✗', 'イ✗ャ✗チ✗セ✗ク✗', 'イ✗ャ✗ブ✗ッ✗ス', 'イ✗ー✗ビ✗オ', 'エO', 'エOい', 'エOスOシO', 'エOチ', 'エO同O', 'エO同O誌', 'エO本', 'エX', 'エXい', 'エXスXシX', 'エXチ', 'エX同X', 'エX同X誌', 'エX本', 'エo', 'エoい', 'エoスoシo', 'エoチ', 'エo同o', 'エo同o誌', 'エo本', 'エx', 'エxい', 'エxスxシx', 'エxチ', 'エx同x', 'エx同x誌', 'エx本', 'エ■', 'エ■い', 'エ■ス■シ■', 'エ■チ', 'エ■同■', 'エ■同■誌', 'エ■本', 'エ□', 'エ□い', 'エ□ス□シ□', 'エ□チ', 'エ□同□', 'エ□同□誌', 'エ□本', 'エ○', 'エ○い', 'エ○ス○シ○', 'エ○チ', 'エ○同○', 'エ○同○誌', 'エ○本', 'エ◯', 'エ◯い', 'エ◯ス◯シ◯', 'エ◯チ', 'エ◯同◯', 'エ◯同◯誌', 'エ◯本', 'エ⚪', 'エ⚪い', 'エ⚪ス⚪シ⚪', 'エ⚪チ', 'エ⚪同⚪', 'エ⚪同⚪誌', 'エ⚪本', 'エ✗', 'エ✗い', 'エ✗ス✗シ✗', 'エ✗チ', 'エ✗同✗', 'エ✗同✗誌', 'エ✗本', 'オOガOム', 'オOニO', 'オOペ', 'オOペOト', 'オOホ', 'オOホOル', 'オXガXム', 'オXニX', 'オXペ', 'オXペXト', 'オXホ', 'オXホXル', 'オoガoム', 'オoニo', 'オoペ', 'オoペoト', 'オoホ', 'オoホoル', 'オxガxム', 'オxニx', 'オxペ', 'オxペxト', 'オxホ', 'オxホxル', 'オ■ガ■ム', 'オ■ニ■', 'オ■ペ', 'オ■ペ■ト', 'オ■ホ', 'オ■ホ■ル', 'オ□ガ□ム', 'オ□ニ□', 'オ□ペ', 'オ□ペ□ト', 'オ□ホ', 'オ□ホ□ル', 'オ○ガ○ム', 'オ○ニ○', 'オ○ペ', 'オ○ペ○ト', 'オ○ホ', 'オ○ホ○ル', 'オ◯ガ◯ム', 'オ◯ニ◯', 'オ◯ペ', 'オ◯ペ◯ト', 'オ◯ホ', 'オ◯ホ◯ル', 'オ⚪ガ⚪ム', 'オ⚪ニ⚪', 'オ⚪ペ', 'オ⚪ペ⚪ト', 'オ⚪ホ', 'オ⚪ホ⚪ル', 'オ✗ガ✗ム', 'オ✗ニ✗', 'オ✗ペ', 'オ✗ペ✗ト', 'オ✗ホ', 'オ✗ホ✗ル', 'カOトO包O', 'カOパO', 'カXトX包X', 'カXパX', 'カoトo包o', 'カoパo', 'カxトx包x', 'カxパx', 'カ■ト■包■', 'カ■パ■', 'カ□ト□包□', 'カ□パ□', 'カ○ト○包○', 'カ○パ○', 'カ◯ト◯包◯', 'カ◯パ◯', 'カ⚪ト⚪包⚪', 'カ⚪パ⚪', 'カ✗ト✗包✗', 'カ✗パ✗', 'キOタO', 'キXタX', 'キoタo', 'キxタx', 'キ■タ■', 'キ□タ□', 'キ○タ○', 'キ◯タ◯', 'キ⚪タ⚪', 'キ✗タ✗', 'ギOグOーO', 'ギXグXーX', 'ギoグoーo', 'ギxグxーx', 'ギ■グ■ー■', 'ギ□グ□ー□', 'ギ○グ○ー○', 'ギ◯グ◯ー◯', 'ギ⚪グ⚪ー⚪', 'ギ✗グ✗ー✗', 'クOガO', 'クOコ', 'クOトOス', 'クOニOンOス', 'クO二', 'クXガX', 'クXコ', 'クXトXス', 'クXニXンXス', 'クX二', 'クoガo', 'クoコ', 'クoトoス', 'クoニoンoス', 'クo二', 'クxガx', 'クxコ', 'クxトxス', 'クxニxンxス', 'クx二', 'ク■ガ■', 'ク■コ', 'ク■ト■ス', 'ク■ニ■ン■ス', 'ク■二', 'ク□ガ□', 'ク□コ', 'ク□ト□ス', 'ク□ニ□ン□ス', 'ク□二', 'ク○ガ○', 'ク○コ', 'ク○ト○ス', 'ク○ニ○ン○ス', 'ク○二', 'ク◯ガ◯', 'ク◯コ', 'ク◯ト◯ス', 'ク◯ニ◯ン◯ス', 'ク◯二', 'ク⚪ガ⚪', 'ク⚪コ', 'ク⚪ト⚪ス', 'ク⚪ニ⚪ン⚪ス', 'ク⚪二', 'ク✗ガ✗', 'ク✗コ', 'ク✗ト✗ス', 'ク✗ニ✗ン✗ス', 'ク✗二', 'ケOマOコ', 'ケXマXコ', 'ケoマoコ', 'ケxマxコ', 'ケ■マ■コ', 'ケ□マ□コ', 'ケ○マ○コ', 'ケ◯マ◯コ', 'ケ⚪マ⚪コ', 'ケ✗マ✗コ', 'コOドOム', 'コXドXム', 'コoドoム', 'コxドxム', 'コ■ド■ム', 'コ□ド□ム', 'コ○ド○ム', 'コ◯ド◯ム', 'コ⚪ド⚪ム', 'コ✗ド✗ム', 'サOマO', 'サXマX', 'サoマo', 'サxマx', 'サ■マ■', 'サ□マ□', 'サ○マ○', 'サ◯マ◯', 'サ⚪マ⚪', 'サ✗マ✗', 'ザOメO', 'ザXメX', 'ザoメo', 'ザxメx', 'ザ■メ■', 'ザ□メ□', 'ザ○メ○', 'ザ◯メ◯', 'ザ⚪メ⚪', 'ザ✗メ✗', 'シOクOナOン', 'シOタOね', 'シXクXナXン', 'シXタXね', 'シoクoナoン', 'シoタoね', 'シxクxナxン', 'シxタxね', 'シ■ク■ナ■ン', 'シ■タ■ね', 'シ□ク□ナ□ン', 'シ□タ□ね', 'シ○ク○ナ○ン', 'シ○タ○ね', 'シ◯ク◯ナ◯ン', 'シ◯タ◯ね', 'シ⚪ク⚪ナ⚪ン', 'シ⚪タ⚪ね', 'シ✗ク✗ナ✗ン', 'シ✗タ✗ね', 'スOッOンO', 'スOトO', 'スOベ', 'スOベO子', 'スOルO', 'スXッXンX', 'スXトX', 'スXベ', 'スXベX子', 'スXルX', 'スoッoンo', 'スoトo', 'スoベ', 'スoベo子', 'スoルo', 'スxッxンx', 'スxトx', 'スxベ', 'スxベx子', 'スxルx', 'ス■ッ■ン■', 'ス■ト■', 'ス■ベ', 'ス■ベ■子', 'ス■ル■', 'ス□ッ□ン□', 'ス□ト□', 'ス□ベ', 'ス□ベ□子', 'ス□ル□', 'ス○ッ○ン○', 'ス○ト○', 'ス○ベ', 'ス○ベ○子', 'ス○ル○', 'ス◯ッ◯ン◯', 'ス◯ト◯', 'ス◯ベ', 'ス◯ベ◯子', 'ス◯ル◯', 'ス⚪ッ⚪ン⚪', 'ス⚪ト⚪', 'ス⚪ベ', 'ス⚪ベ⚪子', 'ス⚪ル⚪', 'ス✗ッ✗ン✗', 'ス✗ト✗', 'ス✗ベ', 'ス✗ベ✗子', 'ス✗ル✗', 'セOクO', 'セOズO', 'セOレ', 'セXクX', 'セXズX', 'セXレ', 'セoクo', 'セoズo', 'セoレ', 'セxクx', 'セxズx', 'セxレ', 'セ■ク■', 'セ■ズ■', 'セ■レ', 'セ□ク□', 'セ□ズ□', 'セ□レ', 'セ○ク○', 'セ○ズ○', 'セ○レ', 'セ◯ク◯', 'セ◯ズ◯', 'セ◯レ', 'セ⚪ク⚪', 'セ⚪ズ⚪', 'セ⚪レ', 'セ✗ク✗', 'セ✗ズ✗', 'セ✗レ', 'ソOトOオO・OマOド', 'ソOプO', 'ソOプOンO', 'ソXトXオX・XマXド', 'ソXプX', 'ソXプXンX', 'ソoトoオo・oマoド', 'ソoプo', 'ソoプoンo', 'ソxトxオx・xマxド', 'ソxプx', 'ソxプxンx', 'ソ■ト■オ■・■マ■ド', 'ソ■プ■', 'ソ■プ■ン■', 'ソ□ト□オ□・□マ□ド', 'ソ□プ□', 'ソ□プ□ン□', 'ソ○ト○オ○・○マ○ド', 'ソ○プ○', 'ソ○プ○ン○', 'ソ◯ト◯オ◯・◯マ◯ド', 'ソ◯プ◯', 'ソ◯プ◯ン◯', 'ソ⚪ト⚪オ⚪・⚪マ⚪ド', 'ソ⚪プ⚪', 'ソ⚪プ⚪ン⚪', 'ソ✗ト✗オ✗・✗マ✗ド', 'ソ✗プ✗', 'ソ✗プ✗ン✗', 'ダOチOイO', 'ダOルOーO', 'ダXチXイX', 'ダXルXーX', 'ダoチoイo', 'ダoルoーo', 'ダxチxイx', 'ダxルxーx', 'ダ■チ■イ■', 'ダ■ル■ー■', 'ダ□チ□イ□', 'ダ□ル□ー□', 'ダ○チ○イ○', 'ダ○ル○ー○', 'ダ◯チ◯イ◯', 'ダ◯ル◯ー◯', 'ダ⚪チ⚪イ⚪', 'ダ⚪ル⚪ー⚪', 'ダ✗チ✗イ✗', 'ダ✗ル✗ー✗', 'チOコ', 'チOチO', 'チOポ', 'チXコ', 'チXチX', 'チXポ', 'チoコ', 'チoチo', 'チoポ', 'チxコ', 'チxチx', 'チxポ', 'チ■コ', 'チ■チ■', 'チ■ポ', 'チ□コ', 'チ□チ□', 'チ□ポ', 'チ○コ', 'チ○チ○', 'チ○ポ', 'チ◯コ', 'チ◯チ◯', 'チ◯ポ', 'チ⚪コ', 'チ⚪チ⚪', 'チ⚪ポ', 'チ✗コ', 'チ✗チ✗', 'チ✗ポ', 'デOチO', 'デOバOーOルO', 'デOヘO', 'デOルO', 'デOーOスOーO', 'デXチX', 'デXバXーXルX', 'デXヘX', 'デXルX', 'デXーXスXーX', 'デoチo', 'デoバoーoルo', 'デoヘo', 'デoルo', 'デoーoスoーo', 'デxチx', 'デxバxーxルx', 'デxヘx', 'デxルx', 'デxーxスxーx', 'デ■チ■', 'デ■バ■ー■ル■', 'デ■ヘ■', 'デ■ル■', 'デ■ー■ス■ー■', 'デ□チ□', 'デ□バ□ー□ル□', 'デ□ヘ□', 'デ□ル□', 'デ□ー□ス□ー□', 'デ○チ○', 'デ○バ○ー○ル○', 'デ○ヘ○', 'デ○ル○', 'デ○ー○ス○ー○', 'デ◯チ◯', 'デ◯バ◯ー◯ル◯', 'デ◯ヘ◯', 'デ◯ル◯', 'デ◯ー◯ス◯ー◯', 'デ⚪チ⚪', 'デ⚪バ⚪ー⚪ル⚪', 'デ⚪ヘ⚪', 'デ⚪ル⚪', 'デ⚪ー⚪ス⚪ー⚪', 'デ✗チ✗', 'デ✗バ✗ー✗ル✗', 'デ✗ヘ✗', 'デ✗ル✗', 'デ✗ー✗ス✗ー✗', 'トO顔', 'トX顔', 'トo顔', 'トx顔', 'ト■顔', 'ト□顔', 'ト○顔', 'ト◯顔', 'ト⚪顔', 'ト✗顔', 'ナOパ', 'ナXパ', 'ナoパ', 'ナxパ', 'ナ■パ', 'ナ□パ', 'ナ○パ', 'ナ◯パ', 'ナ⚪パ', 'ナ✗パ', 'ノOパO', 'ノXパX', 'ノoパo', 'ノxパx', 'ノ■パ■', 'ノ□パ□', 'ノ○パ○', 'ノ◯パ◯', 'ノ⚪パ⚪', 'ノ✗パ✗', 'ハOレO', 'ハO撮O', 'ハXレX', 'ハX撮X', 'ハoレo', 'ハo撮o', 'ハxレx', 'ハx撮x', 'ハ■レ■', 'ハ■撮■', 'ハ□レ□', 'ハ□撮□', 'ハ○レ○', 'ハ○撮○', 'ハ◯レ◯', 'ハ◯撮◯', 'ハ⚪レ⚪', 'ハ⚪撮⚪', 'ハ✗レ✗', 'ハ✗撮✗', 'バOアOラ', 'バOュOムOェO', 'バXアXラ', 'バXュXムXェX', 'バoアoラ', 'バoュoムoェo', 'バxアxラ', 'バxュxムxェx', 'バ■ア■ラ', 'バ■ュ■ム■ェ■', 'バ□ア□ラ', 'バ□ュ□ム□ェ□', 'バ○ア○ラ', 'バ○ュ○ム○ェ○', 'バ◯ア◯ラ', 'バ◯ュ◯ム◯ェ◯', 'バ⚪ア⚪ラ', 'バ⚪ュ⚪ム⚪ェ⚪', 'バ✗ア✗ラ', 'バ✗ュ✗ム✗ェ✗', 'パOズO', 'パOチO', 'パOパO', 'パO活', 'パXズX', 'パXチX', 'パXパX', 'パX活', 'パoズo', 'パoチo', 'パoパo', 'パo活', 'パxズx', 'パxチx', 'パxパx', 'パx活', 'パ■ズ■', 'パ■チ■', 'パ■パ■', 'パ■活', 'パ□ズ□', 'パ□チ□', 'パ□パ□', 'パ□活', 'パ○ズ○', 'パ○チ○', 'パ○パ○', 'パ○活', 'パ◯ズ◯', 'パ◯チ◯', 'パ◯パ◯', 'パ◯活', 'パ⚪ズ⚪', 'パ⚪チ⚪', 'パ⚪パ⚪', 'パ⚪活', 'パ✗ズ✗', 'パ✗チ✗', 'パ✗パ✗', 'パ✗活', 'ビOチ', 'ビXチ', 'ビoチ', 'ビxチ', 'ビ■チ', 'ビ□チ', 'ビ○チ', 'ビ◯チ', 'ビ⚪チ', 'ビ✗チ', 'フOスOフOッO', 'フOラ', 'フOラOき', 'フOラOオ', 'フXスXフXッX', 'フXラ', 'フXラXき', 'フXラXオ', 'フoスoフoッo', 'フoラ', 'フoラoき', 'フoラoオ', 'フxスxフxッx', 'フxラ', 'フxラxき', 'フxラxオ', 'フ■ス■フ■ッ■', 'フ■ラ', 'フ■ラ■き', 'フ■ラ■オ', 'フ□ス□フ□ッ□', 'フ□ラ', 'フ□ラ□き', 'フ□ラ□オ', 'フ○ス○フ○ッ○', 'フ○ラ', 'フ○ラ○き', 'フ○ラ○オ', 'フ◯ス◯フ◯ッ◯', 'フ◯ラ', 'フ◯ラ◯き', 'フ◯ラ◯オ', 'フ⚪ス⚪フ⚪ッ⚪', 'フ⚪ラ', 'フ⚪ラ⚪き', 'フ⚪ラ⚪オ', 'フ✗ス✗フ✗ッ✗', 'フ✗ラ', 'フ✗ラ✗き', 'フ✗ラ✗オ', 'ブOセO', 'ブXセX', 'ブoセo', 'ブxセx', 'ブ■セ■', 'ブ□セ□', 'ブ○セ○', 'ブ◯セ◯', 'ブ⚪セ⚪', 'ブ✗セ✗', 'ペOテOンO', 'ペOバO', 'ペXテXンX', 'ペXバX', 'ペoテoンo', 'ペoバo', 'ペxテxンx', 'ペxバx', 'ペ■テ■ン■', 'ペ■バ■', 'ペ□テ□ン□', 'ペ□バ□', 'ペ○テ○ン○', 'ペ○バ○', 'ペ◯テ◯ン◯', 'ペ◯バ◯', 'ペ⚪テ⚪ン⚪', 'ペ⚪バ⚪', 'ペ✗テ✗ン✗', 'ペ✗バ✗', 'ホO', 'ホX', 'ホo', 'ホx', 'ホ■', 'ホ□', 'ホ○', 'ホ◯', 'ホ⚪', 'ホ✗', 'ボO腹', 'ボX腹', 'ボo腹', 'ボx腹', 'ボ■腹', 'ボ□腹', 'ボ○腹', 'ボ◯腹', 'ボ⚪腹', 'ボ✗腹', 'ポOチO', 'ポXチX', 'ポoチo', 'ポxチx', 'ポ■チ■', 'ポ□チ□', 'ポ○チ○', 'ポ◯チ◯', 'ポ⚪チ⚪', 'ポ✗チ✗', 'マOコ', 'マOタOベOシOン', 'マXコ', 'マXタXベXシXン', 'マoコ', 'マoタoベoシoン', 'マxコ', 'マxタxベxシxン', 'マ■コ', 'マ■タ■ベ■シ■ン', 'マ□コ', 'マ□タ□ベ□シ□ン', 'マ○コ', 'マ○タ○ベ○シ○ン', 'マ◯コ', 'マ◯タ◯ベ◯シ◯ン', 'マ⚪コ', 'マ⚪タ⚪ベ⚪シ⚪ン', 'マ✗コ', 'マ✗タ✗ベ✗シ✗ン', 'ムOムO', 'ムXムX', 'ムoムo', 'ムxムx', 'ム■ム■', 'ム□ム□', 'ム○ム○', 'ム◯ム◯', 'ム⚪ム⚪', 'ム✗ム✗', 'ヤOチO', 'ヤOマO', 'ヤXチX', 'ヤXマX', 'ヤoチo', 'ヤoマo', 'ヤxチx', 'ヤxマx', 'ヤ■チ■', 'ヤ■マ■', 'ヤ□チ□', 'ヤ□マ□', 'ヤ○チ○', 'ヤ○マ○', 'ヤ◯チ◯', 'ヤ◯マ◯', 'ヤ⚪チ⚪', 'ヤ⚪マ⚪', 'ヤ✗チ✗', 'ヤ✗マ✗', 'ラOドOル', 'ラOホ', 'ラOホOル', 'ラXドXル', 'ラXホ', 'ラXホXル', 'ラoドoル', 'ラoホ', 'ラoホoル', 'ラxドxル', 'ラxホ', 'ラxホxル', 'ラ■ド■ル', 'ラ■ホ', 'ラ■ホ■ル', 'ラ□ド□ル', 'ラ□ホ', 'ラ□ホ□ル', 'ラ○ド○ル', 'ラ○ホ', 'ラ○ホ○ル', 'ラ◯ド◯ル', 'ラ◯ホ', 'ラ◯ホ◯ル', 'ラ⚪ド⚪ル', 'ラ⚪ホ', 'ラ⚪ホ⚪ル', 'ラ✗ド✗ル', 'ラ✗ホ', 'ラ✗ホ✗ル', 'リOレ', 'リXレ', 'リoレ', 'リxレ', 'リ■レ', 'リ□レ', 'リ○レ', 'リ◯レ', 'リ⚪レ', 'リ✗レ', 'レOプ', 'レXプ', 'レoプ', 'レxプ', 'レ■プ', 'レ□プ', 'レ○プ', 'レ◯プ', 'レ⚪プ', 'レ✗プ', 'ロOコO', 'ロXコX', 'ロoコo', 'ロxコx', 'ロ■コ■', 'ロ□コ□', 'ロ○コ○', 'ロ◯コ◯', 'ロ⚪コ⚪', 'ロ✗コ✗', '一OＨ', '一XＨ', '一oＨ', '一xＨ', '一■Ｈ', '一□Ｈ', '一○Ｈ', '一◯Ｈ', '一⚪Ｈ', '一✗Ｈ', '中Oし', '中Xし', '中oし', '中xし', '中■し', '中□し', '中○し', '中◯し', '中⚪し', '中✗し', '乙O', '乙X', '乙o', '乙x', '乙■', '乙□', '乙○', '乙◯', '乙⚪', '乙✗', '乱O', '乱O牡O', '乱X', '乱X牡X', '乱o', '乱o牡o', '乱x', '乱x牡x', '乱■', '乱■牡■', '乱□', '乱□牡□', '乱○', '乱○牡○', '乱◯', '乱◯牡◯', '乱⚪', '乱⚪牡⚪', '乱✗', '乱✗牡✗', '乳O', '乳X', '乳o', '乳x', '乳■', '乳□', '乳○', '乳◯', '乳⚪', '乳✗', '亀O', '亀O縛O', '亀X', '亀X縛X', '亀o', '亀o縛o', '亀x', '亀x縛x', '亀■', '亀■縛■', '亀□', '亀□縛□', '亀○', '亀○縛○', '亀◯', '亀◯縛◯', '亀⚪', '亀⚪縛⚪', '亀✗', '亀✗縛✗', '二O', '二O同O', '二X', '二X同X', '二o', '二o同o', '二x', '二x同x', '二■', '二■同■', '二□', '二□同□', '二○', '二○同○', '二◯', '二◯同◯', '二⚪', '二⚪同⚪', '二✗', '二✗同✗', '仮O包O', '仮X包X', '仮o包o', '仮x包x', '仮■包■', '仮□包□', '仮○包○', '仮◯包◯', '仮⚪包⚪', '仮✗包✗', '体O', '体X', '体o', '体x', '体■', '体□', '体○', '体◯', '体⚪', '体✗', '個O撮O', '個X撮X', '個o撮o', '個x撮x', '個■撮■', '個□撮□', '個○撮○', '個◯撮◯', '個⚪撮⚪', '個✗撮✗', '催O', '催X', '催o', '催x', '催■', '催□', '催○', '催◯', '催⚪', '催✗', '兜OわO', '兜XわX', '兜oわo', '兜xわx', '兜■わ■', '兜□わ□', '兜○わ○', '兜◯わ◯', '兜⚪わ⚪', '兜✗わ✗', '入O本O', '入X本X', '入o本o', '入x本x', '入■本■', '入□本□', '入○本○', '入◯本◯', '入⚪本⚪', '入✗本✗', '円O', '円X', '円o', '円x', '円■', '円□', '円○', '円◯', '円⚪', '円✗', '処O', '処X', '処o', '処x', '処■', '処□', '処○', '処◯', '処⚪', '処✗', '包O', '包X', '包o', '包x', '包■', '包□', '包○', '包◯', '包⚪', '包✗', '口O射O', '口O発O', '口X射X', '口X発X', '口o射o', '口o発o', '口x射x', '口x発x', '口■射■', '口■発■', '口□射□', '口□発□', '口○射○', '口○発○', '口◯射◯', '口◯発◯', '口⚪射⚪', '口⚪発⚪', '口✗射✗', '口✗発✗', '唐O居O臼', '唐X居X臼', '唐o居o臼', '唐x居x臼', '唐■居■臼', '唐□居□臼', '唐○居○臼', '唐◯居◯臼', '唐⚪居⚪臼', '唐✗居✗臼', '喘O声', '喘X声', '喘o声', '喘x声', '喘■声', '喘□声', '喘○声', '喘◯声', '喘⚪声', '喘✗声', '四O八O', '四X八X', '四o八o', '四x八x', '四■八■', '四□八□', '四○八○', '四◯八◯', '四⚪八⚪', '四✗八✗', '太OもOキ', '太XもXキ', '太oもoキ', '太xもxキ', '太■も■キ', '太□も□キ', '太○も○キ', '太◯も◯キ', '太⚪も⚪キ', '太✗も✗キ', '姫Oめ', '姫Xめ', '姫oめ', '姫xめ', '姫■め', '姫□め', '姫○め', '姫◯め', '姫⚪め', '姫✗め', '媚O', '媚X', '媚o', '媚x', '媚■', '媚□', '媚○', '媚◯', '媚⚪', '媚✗', '孕Oせ', '孕Xせ', '孕oせ', '孕xせ', '孕■せ', '孕□せ', '孕○せ', '孕◯せ', '孕⚪せ', '孕✗せ', '寝OらO', '寝Oり', '寝XらX', '寝Xり', '寝oらo', '寝oり', '寝xらx', '寝xり', '寝■ら■', '寝■り', '寝□ら□', '寝□り', '寝○ら○', '寝○り', '寝◯ら◯', '寝◯り', '寝⚪ら⚪', '寝⚪り', '寝✗ら✗', '寝✗り', '寿O手', '寿X手', '寿o手', '寿x手', '寿■手', '寿□手', '寿○手', '寿◯手', '寿⚪手', '寿✗手', '射O', '射X', '射o', '射x', '射■', '射□', '射○', '射◯', '射⚪', '射✗', '屍O', '屍X', '屍o', '屍x', '屍■', '屍□', '屍○', '屍◯', '屍⚪', '屍✗', '巨O', '巨X', '巨o', '巨x', '巨■', '巨□', '巨○', '巨◯', '巨⚪', '巨✗', '帆OけO臼', '帆XけX臼', '帆oけo臼', '帆xけx臼', '帆■け■臼', '帆□け□臼', '帆○け○臼', '帆◯け◯臼', '帆⚪け⚪臼', '帆✗け✗臼', '座O', '座X', '座o', '座x', '座■', '座□', '座○', '座◯', '座⚪', '座✗', '強O', '強X', '強o', '強x', '強■', '強□', '強○', '強◯', '強⚪', '強✗', '後O位', '後X位', '後o位', '後x位', '後■位', '後□位', '後○位', '後◯位', '後⚪位', '後✗位', '微O', '微X', '微o', '微x', '微■', '微□', '微○', '微◯', '微⚪', '微✗', '忍O居O臼', '忍X居X臼', '忍o居o臼', '忍x居x臼', '忍■居■臼', '忍□居□臼', '忍○居○臼', '忍◯居◯臼', '忍⚪居⚪臼', '忍✗居✗臼', '快O堕O', '快X堕X', '快o堕o', '快x堕x', '快■堕■', '快□堕□', '快○堕○', '快◯堕◯', '快⚪堕⚪', '快✗堕✗', '性O', '性OマOサOジ', '性O帯', '性O為', '性O理', '性O隷', '性X', '性XマXサXジ', '性X帯', '性X為', '性X理', '性X隷', '性o', '性oマoサoジ', '性o帯', '性o為', '性o理', '性o隷', '性x', '性xマxサxジ', '性x帯', '性x為', '性x理', '性x隷', '性■', '性■マ■サ■ジ', '性■帯', '性■為', '性■理', '性■隷', '性□', '性□マ□サ□ジ', '性□帯', '性□為', '性□理', '性□隷', '性○', '性○マ○サ○ジ', '性○帯', '性○為', '性○理', '性○隷', '性◯', '性◯マ◯サ◯ジ', '性◯帯', '性◯為', '性◯理', '性◯隷', '性⚪', '性⚪マ⚪サ⚪ジ', '性⚪帯', '性⚪為', '性⚪理', '性⚪隷', '性✗', '性✗マ✗サ✗ジ', '性✗帯', '性✗為', '性✗理', '性✗隷', '愛O', '愛X', '愛o', '愛x', '愛■', '愛□', '愛○', '愛◯', '愛⚪', '愛✗', '成O向O', '成X向X', '成o向o', '成x向x', '成■向■', '成□向□', '成○向○', '成◯向◯', '成⚪向⚪', '成✗向✗', '我O汁', '我X汁', '我o汁', '我x汁', '我■汁', '我□汁', '我○汁', '我◯汁', '我⚪汁', '我✗汁', '手O', '手Oキ', '手Oン', '手X', '手Xキ', '手Xン', '手o', '手oキ', '手oン', '手x', '手xキ', '手xン', '手■', '手■キ', '手■ン', '手□', '手□キ', '手□ン', '手○', '手○キ', '手○ン', '手◯', '手◯キ', '手◯ン', '手⚪', '手⚪キ', '手⚪ン', '手✗', '手✗キ', '手✗ン', '抱O地O', '抱X地X', '抱o地o', '抱x地x', '抱■地■', '抱□地□', '抱○地○', '抱◯地◯', '抱⚪地⚪', '抱✗地✗', '揚O本O', '揚X本X', '揚o本o', '揚x本x', '揚■本■', '揚□本□', '揚○本○', '揚◯本◯', '揚⚪本⚪', '揚✗本✗', '援O', '援O交O', '援X', '援X交X', '援o', '援o交o', '援x', '援x交x', '援■', '援■交■', '援□', '援□交□', '援○', '援○交○', '援◯', '援◯交◯', '援⚪', '援⚪交⚪', '援✗', '援✗交✗', '放O', '放OプOイ', '放X', '放XプXイ', '放o', '放oプoイ', '放x', '放xプxイ', '放■', '放■プ■イ', '放□', '放□プ□イ', '放○', '放○プ○イ', '放◯', '放◯プ◯イ', '放⚪', '放⚪プ⚪イ', '放✗', '放✗プ✗イ', '早O', '早X', '早o', '早x', '早■', '早□', '早○', '早◯', '早⚪', '早✗', '時O茶O', '時X茶X', '時o茶o', '時x茶x', '時■茶■', '時□茶□', '時○茶○', '時◯茶◯', '時⚪茶⚪', '時✗茶✗', '月O茶O', '月X茶X', '月o茶o', '月x茶x', '月■茶■', '月□茶□', '月○茶○', '月◯茶◯', '月⚪茶⚪', '月✗茶✗', '朝Oち', '朝Xち', '朝oち', '朝xち', '朝■ち', '朝□ち', '朝○ち', '朝◯ち', '朝⚪ち', '朝✗ち', '松O崩O', '松X崩X', '松o崩o', '松x崩x', '松■崩■', '松□崩□', '松○崩○', '松◯崩◯', '松⚪崩⚪', '松✗崩✗', '機O茶O', '機X茶X', '機o茶o', '機x茶x', '機■茶■', '機□茶□', '機○茶○', '機◯茶◯', '機⚪茶⚪', '機✗茶✗', '正O位', '正X位', '正o位', '正x位', '正■位', '正□位', '正○位', '正◯位', '正⚪位', '正✗位', '汁O優', '汁X優', '汁o優', '汁x優', '汁■優', '汁□優', '汁○優', '汁◯優', '汁⚪優', '汁✗優', '泡O', '泡X', '泡o', '泡x', '泡■', '泡□', '泡○', '泡◯', '泡⚪', '泡✗', '洞OりO手', '洞XりX手', '洞oりo手', '洞xりx手', '洞■り■手', '洞□り□手', '洞○り○手', '洞◯り◯手', '洞⚪り⚪手', '洞✗り✗手', '淫O', '淫X', '淫o', '淫x', '淫■', '淫□', '淫○', '淫◯', '淫⚪', '淫✗', '熟O', '熟X', '熟o', '熟x', '熟■', '熟□', '熟○', '熟◯', '熟⚪', '熟✗', '爆O', '爆X', '爆o', '爆x', '爆■', '爆□', '爆○', '爆◯', '爆⚪', '爆✗', '獣O', '獣X', '獣o', '獣x', '獣■', '獣□', '獣○', '獣◯', '獣⚪', '獣✗', '玉Oめ', '玉Xめ', '玉oめ', '玉xめ', '玉■め', '玉□め', '玉○め', '玉◯め', '玉⚪め', '玉✗め', '生Oメ', '生Xメ', '生oメ', '生xメ', '生■メ', '生□メ', '生○メ', '生◯メ', '生⚪メ', '生✗メ', '男O', '男X', '男o', '男x', '男■', '男□', '男○', '男◯', '男⚪', '男✗', '痴O', '痴X', '痴o', '痴x', '痴■', '痴□', '痴○', '痴◯', '痴⚪', '痴✗', '発O', '発X', '発o', '発x', '発■', '発□', '発○', '発◯', '発⚪', '発✗', '真O包O', '真X包X', '真o包o', '真x包x', '真■包■', '真□包□', '真○包○', '真◯包◯', '真⚪包⚪', '真✗包✗', '睡O', '睡X', '睡o', '睡x', '睡■', '睡□', '睡○', '睡◯', '睡⚪', '睡✗', '睾O', '睾X', '睾o', '睾x', '睾■', '睾□', '睾○', '睾◯', '睾⚪', '睾✗', '種Oけ', '種OけOレO', '種Xけ', '種XけXレX', '種oけ', '種oけoレo', '種xけ', '種xけxレx', '種■け', '種■け■レ■', '種□け', '種□け□レ□', '種○け', '種○け○レ○', '種◯け', '種◯け◯レ◯', '種⚪け', '種⚪け⚪レ⚪', '種✗け', '種✗け✗レ✗', '穴O弟', '穴X弟', '穴o弟', '穴x弟', '穴■弟', '穴□弟', '穴○弟', '穴◯弟', '穴⚪弟', '穴✗弟', '立OんO', '立XんX', '立oんo', '立xんx', '立■ん■', '立□ん□', '立○ん○', '立◯ん◯', '立⚪ん⚪', '立✗ん✗', '童O', '童X', '童o', '童x', '童■', '童□', '童○', '童◯', '童⚪', '童✗', '笠O本O', '笠X本X', '笠o本o', '笠x本x', '笠■本■', '笠□本□', '笠○本○', '笠◯本◯', '笠⚪本⚪', '笠✗本✗', '筆OろO', '筆XろX', '筆oろo', '筆xろx', '筆■ろ■', '筆□ろ□', '筆○ろ○', '筆◯ろ◯', '筆⚪ろ⚪', '筆✗ろ✗', '筏O手', '筏X手', '筏o手', '筏x手', '筏■手', '筏□手', '筏○手', '筏◯手', '筏⚪手', '筏✗手', '粗Oン', '粗Xン', '粗oン', '粗xン', '粗■ン', '粗□ン', '粗○ン', '粗◯ン', '粗⚪ン', '粗✗ン', '素O', '素O ', '素X', '素X ', '素o', '素o ', '素x', '素x ', '素■', '素■ ', '素□', '素□ ', '素○', '素○ ', '素◯', '素◯ ', '素⚪', '素⚪ ', '素✗', '素✗ ', '絶O', '絶X', '絶o', '絶x', '絶■', '絶□', '絶○', '絶◯', '絶⚪', '絶✗', '網O本O', '網X本X', '網o本o', '網x本x', '網■本■', '網□本□', '網○本○', '網◯本◯', '網⚪本⚪', '網✗本✗', '緊O', '緊X', '緊o', '緊x', '緊■', '緊□', '緊○', '緊◯', '緊⚪', '緊✗', '肉O器', '肉X器', '肉o器', '肉x器', '肉■器', '肉□器', '肉○器', '肉◯器', '肉⚪器', '肉✗器', '胸Oラ', '胸Xラ', '胸oラ', '胸xラ', '胸■ラ', '胸□ラ', '胸○ラ', '胸◯ラ', '胸⚪ラ', '胸✗ラ', '脇Oキ', '脇Xキ', '脇oキ', '脇xキ', '脇■キ', '脇□キ', '脇○キ', '脇◯キ', '脇⚪キ', '脇✗キ', '自O', '自X', '自o', '自x', '自■', '自□', '自○', '自◯', '自⚪', '自✗', '菊O', '菊X', '菊o', '菊x', '菊■', '菊□', '菊○', '菊◯', '菊⚪', '菊✗', '蟻O戸Oり', '蟻X戸Xり', '蟻o戸oり', '蟻x戸xり', '蟻■戸■り', '蟻□戸□り', '蟻○戸○り', '蟻◯戸◯り', '蟻⚪戸⚪り', '蟻✗戸✗り', '裏O', '裏X', '裏o', '裏x', '裏■', '裏□', '裏○', '裏◯', '裏⚪', '裏✗', '貝OわO', '貝XわX', '貝oわo', '貝xわx', '貝■わ■', '貝□わ□', '貝○わ○', '貝◯わ◯', '貝⚪わ⚪', '貝✗わ✗', '貧O', '貧X', '貧o', '貧x', '貧■', '貧□', '貧○', '貧◯', '貧⚪', '貧✗', '足Oキ', '足Xキ', '足oキ', '足xキ', '足■キ', '足□キ', '足○キ', '足◯キ', '足⚪キ', '足✗キ', '輪O', '輪X', '輪o', '輪x', '輪■', '輪□', '輪○', '輪◯', '輪⚪', '輪✗', '近O相O', '近X相X', '近o相o', '近x相x', '近■相■', '近□相□', '近○相○', '近◯相◯', '近⚪相⚪', '近✗相✗', '逆OイO', '逆OナO', '逆XイX', '逆XナX', '逆oイo', '逆oナo', '逆xイx', '逆xナx', '逆■イ■', '逆■ナ■', '逆□イ□', '逆□ナ□', '逆○イ○', '逆○ナ○', '逆◯イ◯', '逆◯ナ◯', '逆⚪イ⚪', '逆⚪ナ⚪', '逆✗イ✗', '逆✗ナ✗', '遅O', '遅X', '遅o', '遅x', '遅■', '遅□', '遅○', '遅◯', '遅⚪', '遅✗', '金O', '金X', '金o', '金x', '金■', '金□', '金○', '金◯', '金⚪', '金✗', '陰O', '陰X', '陰o', '陰x', '陰■', '陰□', '陰○', '陰◯', '陰⚪', '陰✗', '陵O', '陵X', '陵o', '陵x', '陵■', '陵□', '陵○', '陵◯', '陵⚪', '陵✗', '雁O首', '雁X首', '雁o首', '雁x首', '雁■首', '雁□首', '雁○首', '雁◯首', '雁⚪首', '雁✗首', '電O', '電X', '電o', '電x', '電■', '電□', '電○', '電◯', '電⚪', '電✗', '青O', '青X', '青o', '青x', '青■', '青□', '青○', '青◯', '青⚪', '青✗', '顔O', '顔X', '顔o', '顔x', '顔■', '顔□', '顔○', '顔◯', '顔⚪', '顔✗', '食O', '食X', '食o', '食x', '食■', '食□', '食○', '食◯', '食⚪', '食✗', '飲O', '飲X', '飲o', '飲x', '飲■', '飲□', '飲○', '飲◯', '飲⚪', '飲✗', '首OきO慕', '首XきX慕', '首oきo慕', '首xきx慕', '首■き■慕', '首□き□慕', '首○き○慕', '首◯き◯慕', '首⚪き⚪慕', '首✗き✗慕', '騎O位', '騎X位', '騎o位', '騎x位', '騎■位', '騎□位', '騎○位', '騎◯位', '騎⚪位', '騎✗位', '鶯O谷Oり', '鶯X谷Xり', '鶯o谷oり', '鶯x谷xり', '鶯■谷■り', '鶯□谷□り', '鶯○谷○り', '鶯◯谷◯り', '鶯⚪谷⚪り', '鶯✗谷✗り', '黄O水', '黄X水', '黄o水', '黄x水', '黄■水', '黄□水', '黄○水', '黄◯水', '黄⚪水', '黄✗水', '黒OャO', '黒XャX', '黒oャo', '黒xャx', '黒■ャ■', '黒□ャ□', '黒○ャ○', '黒◯ャ◯', '黒⚪ャ⚪', '黒✗ャ✗', 'ＳOプOイ', 'ＳXプXイ', 'Ｓoプoイ', 'Ｓxプxイ', 'Ｓ■プ■イ', 'Ｓ□プ□イ', 'Ｓ○プ○イ', 'Ｓ◯プ◯イ', 'Ｓ⚪プ⚪イ', 'Ｓ✗プ✗イ', 'ﾁOﾁO', 'ﾁXﾁX', 'ﾁoﾁo', 'ﾁxﾁx', 'ﾁ■ﾁ■', 'ﾁ□ﾁ□', 'ﾁ○ﾁ○', 'ﾁ◯ﾁ◯', 'ﾁ⚪ﾁ⚪', 'ﾁ✗ﾁ✗']

        async def contains_banned_word_async(text: str) -> bool:
            normalized_text = neologdn.normalize(text)
            all_banned_words = banned_words + banned_words2
            return any(word in normalized_text for word in all_banned_words)

        if await contains_banned_word_async(self.title_.value):
            return await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)
        if await contains_banned_word_async(self.desc.value):
            return await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)
        
        if self.button_label:
            if await contains_banned_word_async(self.button_label.value):
                return await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)
             
        try:
            view = discord.ui.View()
            if self.button.value:
                if self.button_label.value:
                    view.add_item(discord.ui.Button(label=self.button_label.value, url=self.button.value))
                else:
                    view.add_item(discord.ui.Button(label="Webサイト", url=self.button.value))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.blurple, label="作成者の取得", custom_id="showembedowner"))
            await interaction.channel.send(embed=discord.Embed(title=self.title_.value, description=self.desc.value, color=discord.Color.from_str(self.color.value)).set_author(name=f"{interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url).set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.user.default_avatar.url), view=view)
            await interaction.followup.send("作成しました。", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send("作成に失敗しました。", ephemeral=True, embed=discord.Embed(title="エラー内容", description=f"```{e}```", color=discord.Color.red()))
        
class RunContainerMake(discord.ui.Modal, title='Container作成'):
    codeinput = discord.ui.TextInput(
        label='コードを入力',
        placeholder='text:テスト\nline:',
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label='色',
        placeholder='#000000',
        style=discord.TextStyle.short,
        default="#000000"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        banned_words = ['児童', 'sex', 'anal', 'ポルノ', 'エロ', 'セックス', 'ちんこ', 'まんこ', '殺す', '死ね', 'バカ', '吃', '唖', '妾', '嬢', '盲', '聾', '跛', '躄', 'アカ', 'イモ', 'ガキ', 'ガサ', 'キチ', 'キ印', 'クロ', 'サツ', 'シマ', 'スケ', 'チビ', 'デカ', 'ドヤ', 'ノビ', 'ヒモ', 'ブス', 'ブツ', 'ヨツ', '丁稚', '三助', '下女', '下男', '不具', '中共', '乞食', '二号', '人夫', '人足', '令嬢', '低脳', '保母', '傴僂', '北鮮', '南鮮', '土人', '土工', '土方', '坊主', '坑夫', '外人', '女中', '女傑', '女工', '女給', '姦通', '子供', '家柄', '家系', '寄目', '小人', '小僧', '屑屋', '屠殺', '工夫', '床屋', '強姦', '情夫', '情婦', '愚鈍', '按摩', '支那', '文盲', '明盲', '板前', '業病', '正妻', '毛唐', '淫売', '満州', '漁夫', '父兄', '片目', '片端', '片肺', '片親', '片足', '狂う', '狂人', '狂女', '狂気', '猫糞', '獣医', '産婆', '田舎', '番太', '癩病', '白痴', '百姓', '盲人', '盲目', '盲縞', '移民', '穢多', '端女', '精薄', '給仕', '老婆', '職工', '肌色', '色盲', '芸人', '苦力', '虚仮', '血筋', '血統', '親方', '貧農', '身分', '農夫', '近目', '部落', '酋長', '醜男', '鉱夫', '隠坊', '露助', '青姦', '非人', '飯場', '養護', '馬丁', '馬喰', '魚屋', '鮮人', '黒人', 'ＯＬ', 'うんこ', 'お巡り', 'アメ公', 'アル中', 'イタ公', 'オカマ', 'カッペ', 'クンニ', 'コロシ', 'ゴミ屋', 'サラ金', 'ザギン', 'ジャリ', 'ジュー', 'スラム', 'タタキ', 'チョン', 'ドヤ街', 'ナオン', 'ニガー', 'ニグロ', 'ハーフ', 'バタ屋', 'パクる', 'パン助', 'ブタ箱', 'ペイ中', 'ペイ患', 'ポリ公', 'マンコ', 'ヤバい', 'ヤー様', '三つ口', '三国人', '人非人', '代書屋', '低脳児', '借り腹', '八百屋', '共稼ぎ', '処女作', '処女峰', '出戻り', '出稼ぎ', '助産婦', '労務者', '千摺り', '半島人', '名門校', '周旋屋', '四つ足', '四つ辻', '土建屋', '地回り', '女子供', '孤児院', '寄せ場', '小使い', '尻拭い', '屠殺人', '屠殺場', '当て馬', '役不足', '後進国', '心障児', '心障者', '手ん棒', '担ぎ屋', '拡張員', '拡張団', '掃除夫', '掃除婦', '支那人', '支那竹', '新平民', '日雇い', '未亡人', '未開人', '気違い', '沖仲仕', '浮浪児', '浮浪者', '潜水夫', '犬殺し', '町医者', '痴呆症', '皮切り', '皮被り', '盲滅法', '看護婦', '確信犯', '第三国', '紅毛人', '聾桟敷', '脳膜炎', '興信所', '蒙古症', '藪医者', '藪睨み', '蛸部屋', '表日本', '裏日本', '足切り', '踏切番', '連れ子', '過去帳', '郵便夫', '郵便屋', '障害者', '雑役夫', '養老院', '首切り', '黒んぼ', 'あらめん', 'おわい屋', 'かったい', 'がちゃ目', 'ぎっちょ', 'しらっこ', 'ずらかる', 'どさ回り', 'どん百姓', 'ほんぼし', 'ぽん引き', 'まえつき', 'めっかち', 'やさぐれ', 'アイヌ系', 'イカサマ', 'インチキ', 'ゲンナマ', 'ゲーセン', 'ジプシー', 'ジャップ', 'トルコ嬢', 'ニコヨン', 'パーマ屋', 'ポコペン', 'ヤンキー', 'ルンペン', 'ロンパリ', '三韓征伐', '不可触民', '不治の病', '他力本願', '伊勢乞食', '低開発国', '保線工夫', '台湾ハゲ', '台湾政府', '合いの子', '土左衛門', '垂れ流す', '士農工商', '婿をとる', '嫁にやる', '川向こう', '引かれ者', '拡張団長', '支那料理', '支那蕎麦', '朝鮮人参', '朝鮮征伐', '未開発国', '植物人間', '河原乞食', '溺れ死ぬ', '滑り止め', '片手落ち', '特殊学校', '特殊学級', '特殊部落', '発狂する', '盲愛する', '知恵遅れ', '精神異常', '線路工夫', '自閉症児', '落とし前', '落人部落', '足を洗う', '身元調査', '運ちゃん', '釣り書き', '魔女っ子', 'いちゃもん', 'かさっかき', 'くわえ込む', 'すけこまし', 'エスキモー', 'エディター', 'ズージャー', 'ダッチマン', 'チャリンコ', 'チャンコロ', 'トルコ風呂', 'ポッポー屋', '上方の贅六', '富山の三助', '気違い沙汰', '汲み取り屋', '灸を据える', '狂気の沙汰', '玉袋筋太郎', '盲判を押す', '精神分裂病', '股に掛ける', '育ちより氏', '落ちこぼれ', '蛙の子は蛙', 'がっぷり四つ', 'オールドミス', 'サラブレッド', 'タケノコ医者', '娘を片付ける', '本腰を入れる', '気違いに刃物', '盲蛇に怖じず', '越後の米つき', 'エチゼンクラゲ', 'スチュワーデス', 'レントゲン技師', '将棋倒しになる', '日本のチベット', '群盲象をなでる', 'ブラインドタッチ', '女の腐ったような', '馬鹿チョンカメラ', '南部の鮭の鼻まがり', '天才と狂人は紙一重', '馬鹿でもチョンでも', 'インディアン嘘つかない', '健全なる精神は健全なる身体に宿る', 'NTR', 'NㄒR', 'Tバック', 'えっち', 'えっㄎ', 'えっㄘ', 'おちんちん', 'おㄎんㄎん', 'おㄘんㄘん', 'さかさ椋鳥', 'せきれい本手', 'せっくす', 'せっㄑす', 'だいしゅきホールド', 'だいしゅきホーㄦド', 'ちんこ', 'ちんちん', 'ちんぽ', 'ひとりえっち', 'ひとりえっㄎ', 'ひとりえっㄘ', 'アクメ', 'アクㄨ', 'アダルトビデオ', 'アダㄦトビデオ', 'アナル', 'アナルセックス', 'アナルビーズ', 'アナルプラグ', 'アナル拡張', 'アナル開発', 'アナルＳＥＸ', 'アナㄦ', 'アナㄦセックス', 'アナㄦビーズ', 'アナㄦプラグ', 'アナㄦ拡張', 'アナㄦ開発', 'アナㄦＳＥＸ', 'イメクラ', 'イメージビデオ', 'イㄨクラ', 'イㄨージビデオ', 'エクスタシー', 'エッチ', 'エロ', 'エロい', 'エロ同人', 'エロ同人誌', 'エロ本', 'オナホール', 'オナホーㄦ', 'オーガズム', 'オーガズㄊ', 'オーガズㄙ', 'カウパー', 'カントン包茎', 'ギャグボール', 'ギャグボーㄦ', 'コンドーム', 'コンドーㄊ', 'コンドーㄙ', 'ザーメン', 'ザーㄨン', 'スカトロ', 'スペルマ', 'スペㄦマ', 'スㄌトロ', 'ダブルピース', 'ダブㄦピース', 'ディルド', 'ディㄦド', 'デカチン', 'デリバリーヘルス', 'デリバリーヘㄦス', 'デリヘル', 'デリヘㄦ', 'デㄌチン', 'ハメ撮り', 'ハーレム', 'ハーレㄊ', 'ハーレㄙ', 'ハㄨ撮り', 'バキュームフェラ', 'バキューㄊフェラ', 'バキューㄙフェラ', 'ブルセラ', 'ブㄦセラ', 'ポルチオ', 'ポㄦチオ', 'ムラムラ', 'ラブドール', 'ラブドーㄦ', 'ラブホテル', 'ラブホテㄦ', 'ㄊラㄊラ', 'ㄌウパー', 'ㄌントン包茎', 'ㄎんこ', 'ㄎんぽ', 'ㄎんㄎん', 'ㄒバック', 'ㄘんこ', 'ㄘんぽ', 'ㄘんㄘん', 'ㄙラㄙラ', 'ㄛかㄛ椋鳥', 'ㄜかㄜ椋鳥', 'ㄝきれい本手', 'ㄝっくす', 'ㄝっㄑす', 'ㆥきれい本手', 'ㆥっくす', 'ㆥっㄑす', 'ㆲクスタシー', 'ㆲッチ', 'ㆲロ', 'ㆲロい', 'ㆲロ同人', 'ㆲロ同人誌', 'ㆲロ本', '兜合わせ', '兜合わㄝ', '兜合わㆥ', '孕ませ', '孕まㄝ', '孕まㆥ', '快楽堕ち', '快楽堕ㄎ', '快楽堕ㄘ', '朝勃ち', '朝勃ㄎ', '朝勃ㄘ', '朝起ち', '朝起ㄎ', '朝起ㄘ', '生ハメ', '生ハㄨ', '立ちんぼ', '立ㄎんぼ', '立ㄘんぼ', '筆おろし', '筆おㄋし', '貝合わせ', '貝合わㄝ', '貝合わㆥ', '逆アナル', '逆アナㄦ', '黒ギャル', '黒ギャㄦ']
        banned_words2 = ['3O', '3X', '3o', '3x', '3■', '3□', '3○', '3◯', '3⚪', '3✗', 'AO女O', 'AX女X', 'Ao女o', 'Ax女x', 'A■女■', 'A□女□', 'A○女○', 'A◯女◯', 'A⚪女⚪', 'A✗女✗', 'GOポOト', 'GXポXト', 'Goポoト', 'Gxポxト', 'G■ポ■ト', 'G□ポ□ト', 'G○ポ○ト', 'G◯ポ◯ト', 'G⚪ポ⚪ト', 'G✗ポ✗ト', 'NOR', 'NXR', 'NoR', 'NxR', 'N■R', 'N□R', 'N○R', 'N◯R', 'N⚪R', 'N✗R', 'SO', 'SOD', 'SOX', 'SX', 'SXD', 'SXX', 'So', 'SoD', 'SoX', 'Sx', 'SxD', 'SxX', 'S■', 'S■D', 'S■X', 'S□', 'S□D', 'S□X', 'S○', 'S○D', 'S○X', 'S◯', 'S◯D', 'S◯X', 'S⚪', 'S⚪D', 'S⚪X', 'S✗', 'S✗D', 'S✗X', 'TOッO', 'TXッX', 'Toッo', 'Txッx', 'T■ッ■', 'T□ッ□', 'T○ッ○', 'T◯ッ◯', 'T⚪ッ⚪', 'T✗ッ✗', 'いOらOい', 'いXらXい', 'いoらoい', 'いxらxい', 'い■ら■い', 'い□ら□い', 'い○ら○い', 'い◯ら◯い', 'い⚪ら⚪い', 'い✗ら✗い', 'えOち', 'えXち', 'えoち', 'えxち', 'え■ち', 'え□ち', 'え○ち', 'え◯ち', 'え⚪ち', 'え✗ち', 'おOπ', 'おOこ', 'おOにO', 'おOぱO', 'おOんO', 'おOんOん', 'おOシOタ', 'おO除OェO', 'おXπ', 'おXこ', 'おXにX', 'おXぱX', 'おXんX', 'おXんXん', 'おXシXタ', 'おX除XェX', 'おoπ', 'おoこ', 'おoにo', 'おoぱo', 'おoんo', 'おoんoん', 'おoシoタ', 'おo除oェo', 'おxπ', 'おxこ', 'おxにx', 'おxぱx', 'おxんx', 'おxんxん', 'おxシxタ', 'おx除xェx', 'お■π', 'お■こ', 'お■に■', 'お■ぱ■', 'お■ん■', 'お■ん■ん', 'お■シ■タ', 'お■除■ェ■', 'お□π', 'お□こ', 'お□に□', 'お□ぱ□', 'お□ん□', 'お□ん□ん', 'お□シ□タ', 'お□除□ェ□', 'お○π', 'お○こ', 'お○に○', 'お○ぱ○', 'お○ん○', 'お○ん○ん', 'お○シ○タ', 'お○除○ェ○', 'お◯π', 'お◯こ', 'お◯に◯', 'お◯ぱ◯', 'お◯ん◯', 'お◯ん◯ん', 'お◯シ◯タ', 'お◯除◯ェ◯', 'お⚪π', 'お⚪こ', 'お⚪に⚪', 'お⚪ぱ⚪', 'お⚪ん⚪', 'お⚪ん⚪ん', 'お⚪シ⚪タ', 'お⚪除⚪ェ⚪', 'お✗π', 'お✗こ', 'お✗に✗', 'お✗ぱ✗', 'お✗ん✗', 'お✗ん✗ん', 'お✗シ✗タ', 'お✗除✗ェ✗', 'きOたO', 'きXたX', 'きoたo', 'きxたx', 'き■た■', 'き□た□', 'き○た○', 'き◯た◯', 'き⚪た⚪', 'き✗た✗', 'さOさO鳥', 'さXさX鳥', 'さoさo鳥', 'さxさx鳥', 'さ■さ■鳥', 'さ□さ□鳥', 'さ○さ○鳥', 'さ◯さ◯鳥', 'さ⚪さ⚪鳥', 'さ✗さ✗鳥', 'しOりO蓉', 'しXりX蓉', 'しoりo蓉', 'しxりx蓉', 'し■り■蓉', 'し□り□蓉', 'し○り○蓉', 'し◯り◯蓉', 'し⚪り⚪蓉', 'し✗り✗蓉', 'すOべ', 'すXべ', 'すoべ', 'すxべ', 'す■べ', 'す□べ', 'す○べ', 'す◯べ', 'す⚪べ', 'す✗べ', 'せOくO', 'せOれO本O', 'せXくX', 'せXれX本X', 'せoくo', 'せoれo本o', 'せxくx', 'せxれx本x', 'せ■く■', 'せ■れ■本■', 'せ□く□', 'せ□れ□本□', 'せ○く○', 'せ○れ○本○', 'せ◯く◯', 'せ◯れ◯本◯', 'せ⚪く⚪', 'せ⚪れ⚪本⚪', 'せ✗く✗', 'せ✗れ✗本✗', 'だOしOきOーOド', 'だXしXきXーXド', 'だoしoきoーoド', 'だxしxきxーxド', 'だ■し■き■ー■ド', 'だ□し□き□ー□ド', 'だ○し○き○ー○ド', 'だ◯し◯き◯ー◯ド', 'だ⚪し⚪き⚪ー⚪ド', 'だ✗し✗き✗ー✗ド', 'ちOこ', 'ちOちO', 'ちOぽ', 'ちXこ', 'ちXちX', 'ちXぽ', 'ちoこ', 'ちoちo', 'ちoぽ', 'ちxこ', 'ちxちx', 'ちxぽ', 'ち■こ', 'ち■ち■', 'ち■ぽ', 'ち□こ', 'ち□ち□', 'ち□ぽ', 'ち○こ', 'ち○ち○', 'ち○ぽ', 'ち◯こ', 'ち◯ち◯', 'ち◯ぽ', 'ち⚪こ', 'ち⚪ち⚪', 'ち⚪ぽ', 'ち✗こ', 'ち✗ち✗', 'ち✗ぽ', 'ひOりOっO', 'ひXりXっX', 'ひoりoっo', 'ひxりxっx', 'ひ■り■っ■', 'ひ□り□っ□', 'ひ○り○っ○', 'ひ◯り◯っ◯', 'ひ⚪り⚪っ⚪', 'ひ✗り✗っ✗', 'ふOなO', 'ふXなX', 'ふoなo', 'ふxなx', 'ふ■な■', 'ふ□な□', 'ふ○な○', 'ふ◯な◯', 'ふ⚪な⚪', 'ふ✗な✗', 'まOぐO返O', 'まOこ', 'まOまO', 'まXぐX返X', 'まXこ', 'まXまX', 'まoぐo返o', 'まoこ', 'まoまo', 'まxぐx返x', 'まxこ', 'まxまx', 'ま■ぐ■返■', 'ま■こ', 'ま■ま■', 'ま□ぐ□返□', 'ま□こ', 'ま□ま□', 'ま○ぐ○返○', 'ま○こ', 'ま○ま○', 'ま◯ぐ◯返◯', 'ま◯こ', 'ま◯ま◯', 'ま⚪ぐ⚪返⚪', 'ま⚪こ', 'ま⚪ま⚪', 'ま✗ぐ✗返✗', 'ま✗こ', 'ま✗ま✗', 'むOむO', 'むXむX', 'むoむo', 'むxむx', 'む■む■', 'む□む□', 'む○む○', 'む◯む◯', 'む⚪む⚪', 'む✗む✗', 'アOニO', 'アOマO', 'アOメ', 'アOル', 'アOルOッOス', 'アOルOビOオ', 'アOルOラO', 'アOルOーO', 'アOルO張', 'アOルO発', 'アOルOＥO', 'アO顔', 'アXニX', 'アXマX', 'アXメ', 'アXル', 'アXルXッXス', 'アXルXビXオ', 'アXルXラX', 'アXルXーX', 'アXルX張', 'アXルX発', 'アXルXＥX', 'アX顔', 'アoニo', 'アoマo', 'アoメ', 'アoル', 'アoルoッoス', 'アoルoビoオ', 'アoルoラo', 'アoルoーo', 'アoルo張', 'アoルo発', 'アoルoＥo', 'アo顔', 'アxニx', 'アxマx', 'アxメ', 'アxル', 'アxルxッxス', 'アxルxビxオ', 'アxルxラx', 'アxルxーx', 'アxルx張', 'アxルx発', 'アxルxＥx', 'アx顔', 'ア■ニ■', 'ア■マ■', 'ア■メ', 'ア■ル', 'ア■ル■ッ■ス', 'ア■ル■ビ■オ', 'ア■ル■ラ■', 'ア■ル■ー■', 'ア■ル■張', 'ア■ル■発', 'ア■ル■Ｅ■', 'ア■顔', 'ア□ニ□', 'ア□マ□', 'ア□メ', 'ア□ル', 'ア□ル□ッ□ス', 'ア□ル□ビ□オ', 'ア□ル□ラ□', 'ア□ル□ー□', 'ア□ル□張', 'ア□ル□発', 'ア□ル□Ｅ□', 'ア□顔', 'ア○ニ○', 'ア○マ○', 'ア○メ', 'ア○ル', 'ア○ル○ッ○ス', 'ア○ル○ビ○オ', 'ア○ル○ラ○', 'ア○ル○ー○', 'ア○ル○張', 'ア○ル○発', 'ア○ル○Ｅ○', 'ア○顔', 'ア◯ニ◯', 'ア◯マ◯', 'ア◯メ', 'ア◯ル', 'ア◯ル◯ッ◯ス', 'ア◯ル◯ビ◯オ', 'ア◯ル◯ラ◯', 'ア◯ル◯ー◯', 'ア◯ル◯張', 'ア◯ル◯発', 'ア◯ル◯Ｅ◯', 'ア◯顔', 'ア⚪ニ⚪', 'ア⚪マ⚪', 'ア⚪メ', 'ア⚪ル', 'ア⚪ル⚪ッ⚪ス', 'ア⚪ル⚪ビ⚪オ', 'ア⚪ル⚪ラ⚪', 'ア⚪ル⚪ー⚪', 'ア⚪ル⚪張', 'ア⚪ル⚪発', 'ア⚪ル⚪Ｅ⚪', 'ア⚪顔', 'ア✗ニ✗', 'ア✗マ✗', 'ア✗メ', 'ア✗ル', 'ア✗ル✗ッ✗ス', 'ア✗ル✗ビ✗オ', 'ア✗ル✗ラ✗', 'ア✗ル✗ー✗', 'ア✗ル✗張', 'ア✗ル✗発', 'ア✗ル✗Ｅ✗', 'ア✗顔', 'イO', 'イOクO', 'イOポ', 'イOポOンO', 'イOマOオ', 'イOモO', 'イOャOチOセOクO', 'イOャOブOッOス', 'イOーOビOオ', 'イX', 'イXクX', 'イXポ', 'イXポXンX', 'イXマXオ', 'イXモX', 'イXャXチXセXクX', 'イXャXブXッXス', 'イXーXビXオ', 'イo', 'イoクo', 'イoポ', 'イoポoンo', 'イoマoオ', 'イoモo', 'イoャoチoセoクo', 'イoャoブoッoス', 'イoーoビoオ', 'イx', 'イxクx', 'イxポ', 'イxポxンx', 'イxマxオ', 'イxモx', 'イxャxチxセxクx', 'イxャxブxッxス', 'イxーxビxオ', 'イ■', 'イ■ク■', 'イ■ポ', 'イ■ポ■ン■', 'イ■マ■オ', 'イ■モ■', 'イ■ャ■チ■セ■ク■', 'イ■ャ■ブ■ッ■ス', 'イ■ー■ビ■オ', 'イ□', 'イ□ク□', 'イ□ポ', 'イ□ポ□ン□', 'イ□マ□オ', 'イ□モ□', 'イ□ャ□チ□セ□ク□', 'イ□ャ□ブ□ッ□ス', 'イ□ー□ビ□オ', 'イ○', 'イ○ク○', 'イ○ポ', 'イ○ポ○ン○', 'イ○マ○オ', 'イ○モ○', 'イ○ャ○チ○セ○ク○', 'イ○ャ○ブ○ッ○ス', 'イ○ー○ビ○オ', 'イ◯', 'イ◯ク◯', 'イ◯ポ', 'イ◯ポ◯ン◯', 'イ◯マ◯オ', 'イ◯モ◯', 'イ◯ャ◯チ◯セ◯ク◯', 'イ◯ャ◯ブ◯ッ◯ス', 'イ◯ー◯ビ◯オ', 'イ⚪', 'イ⚪ク⚪', 'イ⚪ポ', 'イ⚪ポ⚪ン⚪', 'イ⚪マ⚪オ', 'イ⚪モ⚪', 'イ⚪ャ⚪チ⚪セ⚪ク⚪', 'イ⚪ャ⚪ブ⚪ッ⚪ス', 'イ⚪ー⚪ビ⚪オ', 'イ✗', 'イ✗ク✗', 'イ✗ポ', 'イ✗ポ✗ン✗', 'イ✗マ✗オ', 'イ✗モ✗', 'イ✗ャ✗チ✗セ✗ク✗', 'イ✗ャ✗ブ✗ッ✗ス', 'イ✗ー✗ビ✗オ', 'エO', 'エOい', 'エOスOシO', 'エOチ', 'エO同O', 'エO同O誌', 'エO本', 'エX', 'エXい', 'エXスXシX', 'エXチ', 'エX同X', 'エX同X誌', 'エX本', 'エo', 'エoい', 'エoスoシo', 'エoチ', 'エo同o', 'エo同o誌', 'エo本', 'エx', 'エxい', 'エxスxシx', 'エxチ', 'エx同x', 'エx同x誌', 'エx本', 'エ■', 'エ■い', 'エ■ス■シ■', 'エ■チ', 'エ■同■', 'エ■同■誌', 'エ■本', 'エ□', 'エ□い', 'エ□ス□シ□', 'エ□チ', 'エ□同□', 'エ□同□誌', 'エ□本', 'エ○', 'エ○い', 'エ○ス○シ○', 'エ○チ', 'エ○同○', 'エ○同○誌', 'エ○本', 'エ◯', 'エ◯い', 'エ◯ス◯シ◯', 'エ◯チ', 'エ◯同◯', 'エ◯同◯誌', 'エ◯本', 'エ⚪', 'エ⚪い', 'エ⚪ス⚪シ⚪', 'エ⚪チ', 'エ⚪同⚪', 'エ⚪同⚪誌', 'エ⚪本', 'エ✗', 'エ✗い', 'エ✗ス✗シ✗', 'エ✗チ', 'エ✗同✗', 'エ✗同✗誌', 'エ✗本', 'オOガOム', 'オOニO', 'オOペ', 'オOペOト', 'オOホ', 'オOホOル', 'オXガXム', 'オXニX', 'オXペ', 'オXペXト', 'オXホ', 'オXホXル', 'オoガoム', 'オoニo', 'オoペ', 'オoペoト', 'オoホ', 'オoホoル', 'オxガxム', 'オxニx', 'オxペ', 'オxペxト', 'オxホ', 'オxホxル', 'オ■ガ■ム', 'オ■ニ■', 'オ■ペ', 'オ■ペ■ト', 'オ■ホ', 'オ■ホ■ル', 'オ□ガ□ム', 'オ□ニ□', 'オ□ペ', 'オ□ペ□ト', 'オ□ホ', 'オ□ホ□ル', 'オ○ガ○ム', 'オ○ニ○', 'オ○ペ', 'オ○ペ○ト', 'オ○ホ', 'オ○ホ○ル', 'オ◯ガ◯ム', 'オ◯ニ◯', 'オ◯ペ', 'オ◯ペ◯ト', 'オ◯ホ', 'オ◯ホ◯ル', 'オ⚪ガ⚪ム', 'オ⚪ニ⚪', 'オ⚪ペ', 'オ⚪ペ⚪ト', 'オ⚪ホ', 'オ⚪ホ⚪ル', 'オ✗ガ✗ム', 'オ✗ニ✗', 'オ✗ペ', 'オ✗ペ✗ト', 'オ✗ホ', 'オ✗ホ✗ル', 'カOトO包O', 'カOパO', 'カXトX包X', 'カXパX', 'カoトo包o', 'カoパo', 'カxトx包x', 'カxパx', 'カ■ト■包■', 'カ■パ■', 'カ□ト□包□', 'カ□パ□', 'カ○ト○包○', 'カ○パ○', 'カ◯ト◯包◯', 'カ◯パ◯', 'カ⚪ト⚪包⚪', 'カ⚪パ⚪', 'カ✗ト✗包✗', 'カ✗パ✗', 'キOタO', 'キXタX', 'キoタo', 'キxタx', 'キ■タ■', 'キ□タ□', 'キ○タ○', 'キ◯タ◯', 'キ⚪タ⚪', 'キ✗タ✗', 'ギOグOーO', 'ギXグXーX', 'ギoグoーo', 'ギxグxーx', 'ギ■グ■ー■', 'ギ□グ□ー□', 'ギ○グ○ー○', 'ギ◯グ◯ー◯', 'ギ⚪グ⚪ー⚪', 'ギ✗グ✗ー✗', 'クOガO', 'クOコ', 'クOトOス', 'クOニOンOス', 'クO二', 'クXガX', 'クXコ', 'クXトXス', 'クXニXンXス', 'クX二', 'クoガo', 'クoコ', 'クoトoス', 'クoニoンoス', 'クo二', 'クxガx', 'クxコ', 'クxトxス', 'クxニxンxス', 'クx二', 'ク■ガ■', 'ク■コ', 'ク■ト■ス', 'ク■ニ■ン■ス', 'ク■二', 'ク□ガ□', 'ク□コ', 'ク□ト□ス', 'ク□ニ□ン□ス', 'ク□二', 'ク○ガ○', 'ク○コ', 'ク○ト○ス', 'ク○ニ○ン○ス', 'ク○二', 'ク◯ガ◯', 'ク◯コ', 'ク◯ト◯ス', 'ク◯ニ◯ン◯ス', 'ク◯二', 'ク⚪ガ⚪', 'ク⚪コ', 'ク⚪ト⚪ス', 'ク⚪ニ⚪ン⚪ス', 'ク⚪二', 'ク✗ガ✗', 'ク✗コ', 'ク✗ト✗ス', 'ク✗ニ✗ン✗ス', 'ク✗二', 'ケOマOコ', 'ケXマXコ', 'ケoマoコ', 'ケxマxコ', 'ケ■マ■コ', 'ケ□マ□コ', 'ケ○マ○コ', 'ケ◯マ◯コ', 'ケ⚪マ⚪コ', 'ケ✗マ✗コ', 'コOドOム', 'コXドXム', 'コoドoム', 'コxドxム', 'コ■ド■ム', 'コ□ド□ム', 'コ○ド○ム', 'コ◯ド◯ム', 'コ⚪ド⚪ム', 'コ✗ド✗ム', 'サOマO', 'サXマX', 'サoマo', 'サxマx', 'サ■マ■', 'サ□マ□', 'サ○マ○', 'サ◯マ◯', 'サ⚪マ⚪', 'サ✗マ✗', 'ザOメO', 'ザXメX', 'ザoメo', 'ザxメx', 'ザ■メ■', 'ザ□メ□', 'ザ○メ○', 'ザ◯メ◯', 'ザ⚪メ⚪', 'ザ✗メ✗', 'シOクOナOン', 'シOタOね', 'シXクXナXン', 'シXタXね', 'シoクoナoン', 'シoタoね', 'シxクxナxン', 'シxタxね', 'シ■ク■ナ■ン', 'シ■タ■ね', 'シ□ク□ナ□ン', 'シ□タ□ね', 'シ○ク○ナ○ン', 'シ○タ○ね', 'シ◯ク◯ナ◯ン', 'シ◯タ◯ね', 'シ⚪ク⚪ナ⚪ン', 'シ⚪タ⚪ね', 'シ✗ク✗ナ✗ン', 'シ✗タ✗ね', 'スOッOンO', 'スOトO', 'スOベ', 'スOベO子', 'スOルO', 'スXッXンX', 'スXトX', 'スXベ', 'スXベX子', 'スXルX', 'スoッoンo', 'スoトo', 'スoベ', 'スoベo子', 'スoルo', 'スxッxンx', 'スxトx', 'スxベ', 'スxベx子', 'スxルx', 'ス■ッ■ン■', 'ス■ト■', 'ス■ベ', 'ス■ベ■子', 'ス■ル■', 'ス□ッ□ン□', 'ス□ト□', 'ス□ベ', 'ス□ベ□子', 'ス□ル□', 'ス○ッ○ン○', 'ス○ト○', 'ス○ベ', 'ス○ベ○子', 'ス○ル○', 'ス◯ッ◯ン◯', 'ス◯ト◯', 'ス◯ベ', 'ス◯ベ◯子', 'ス◯ル◯', 'ス⚪ッ⚪ン⚪', 'ス⚪ト⚪', 'ス⚪ベ', 'ス⚪ベ⚪子', 'ス⚪ル⚪', 'ス✗ッ✗ン✗', 'ス✗ト✗', 'ス✗ベ', 'ス✗ベ✗子', 'ス✗ル✗', 'セOクO', 'セOズO', 'セOレ', 'セXクX', 'セXズX', 'セXレ', 'セoクo', 'セoズo', 'セoレ', 'セxクx', 'セxズx', 'セxレ', 'セ■ク■', 'セ■ズ■', 'セ■レ', 'セ□ク□', 'セ□ズ□', 'セ□レ', 'セ○ク○', 'セ○ズ○', 'セ○レ', 'セ◯ク◯', 'セ◯ズ◯', 'セ◯レ', 'セ⚪ク⚪', 'セ⚪ズ⚪', 'セ⚪レ', 'セ✗ク✗', 'セ✗ズ✗', 'セ✗レ', 'ソOトOオO・OマOド', 'ソOプO', 'ソOプOンO', 'ソXトXオX・XマXド', 'ソXプX', 'ソXプXンX', 'ソoトoオo・oマoド', 'ソoプo', 'ソoプoンo', 'ソxトxオx・xマxド', 'ソxプx', 'ソxプxンx', 'ソ■ト■オ■・■マ■ド', 'ソ■プ■', 'ソ■プ■ン■', 'ソ□ト□オ□・□マ□ド', 'ソ□プ□', 'ソ□プ□ン□', 'ソ○ト○オ○・○マ○ド', 'ソ○プ○', 'ソ○プ○ン○', 'ソ◯ト◯オ◯・◯マ◯ド', 'ソ◯プ◯', 'ソ◯プ◯ン◯', 'ソ⚪ト⚪オ⚪・⚪マ⚪ド', 'ソ⚪プ⚪', 'ソ⚪プ⚪ン⚪', 'ソ✗ト✗オ✗・✗マ✗ド', 'ソ✗プ✗', 'ソ✗プ✗ン✗', 'ダOチOイO', 'ダOルOーO', 'ダXチXイX', 'ダXルXーX', 'ダoチoイo', 'ダoルoーo', 'ダxチxイx', 'ダxルxーx', 'ダ■チ■イ■', 'ダ■ル■ー■', 'ダ□チ□イ□', 'ダ□ル□ー□', 'ダ○チ○イ○', 'ダ○ル○ー○', 'ダ◯チ◯イ◯', 'ダ◯ル◯ー◯', 'ダ⚪チ⚪イ⚪', 'ダ⚪ル⚪ー⚪', 'ダ✗チ✗イ✗', 'ダ✗ル✗ー✗', 'チOコ', 'チOチO', 'チOポ', 'チXコ', 'チXチX', 'チXポ', 'チoコ', 'チoチo', 'チoポ', 'チxコ', 'チxチx', 'チxポ', 'チ■コ', 'チ■チ■', 'チ■ポ', 'チ□コ', 'チ□チ□', 'チ□ポ', 'チ○コ', 'チ○チ○', 'チ○ポ', 'チ◯コ', 'チ◯チ◯', 'チ◯ポ', 'チ⚪コ', 'チ⚪チ⚪', 'チ⚪ポ', 'チ✗コ', 'チ✗チ✗', 'チ✗ポ', 'デOチO', 'デOバOーOルO', 'デOヘO', 'デOルO', 'デOーOスOーO', 'デXチX', 'デXバXーXルX', 'デXヘX', 'デXルX', 'デXーXスXーX', 'デoチo', 'デoバoーoルo', 'デoヘo', 'デoルo', 'デoーoスoーo', 'デxチx', 'デxバxーxルx', 'デxヘx', 'デxルx', 'デxーxスxーx', 'デ■チ■', 'デ■バ■ー■ル■', 'デ■ヘ■', 'デ■ル■', 'デ■ー■ス■ー■', 'デ□チ□', 'デ□バ□ー□ル□', 'デ□ヘ□', 'デ□ル□', 'デ□ー□ス□ー□', 'デ○チ○', 'デ○バ○ー○ル○', 'デ○ヘ○', 'デ○ル○', 'デ○ー○ス○ー○', 'デ◯チ◯', 'デ◯バ◯ー◯ル◯', 'デ◯ヘ◯', 'デ◯ル◯', 'デ◯ー◯ス◯ー◯', 'デ⚪チ⚪', 'デ⚪バ⚪ー⚪ル⚪', 'デ⚪ヘ⚪', 'デ⚪ル⚪', 'デ⚪ー⚪ス⚪ー⚪', 'デ✗チ✗', 'デ✗バ✗ー✗ル✗', 'デ✗ヘ✗', 'デ✗ル✗', 'デ✗ー✗ス✗ー✗', 'トO顔', 'トX顔', 'トo顔', 'トx顔', 'ト■顔', 'ト□顔', 'ト○顔', 'ト◯顔', 'ト⚪顔', 'ト✗顔', 'ナOパ', 'ナXパ', 'ナoパ', 'ナxパ', 'ナ■パ', 'ナ□パ', 'ナ○パ', 'ナ◯パ', 'ナ⚪パ', 'ナ✗パ', 'ノOパO', 'ノXパX', 'ノoパo', 'ノxパx', 'ノ■パ■', 'ノ□パ□', 'ノ○パ○', 'ノ◯パ◯', 'ノ⚪パ⚪', 'ノ✗パ✗', 'ハOレO', 'ハO撮O', 'ハXレX', 'ハX撮X', 'ハoレo', 'ハo撮o', 'ハxレx', 'ハx撮x', 'ハ■レ■', 'ハ■撮■', 'ハ□レ□', 'ハ□撮□', 'ハ○レ○', 'ハ○撮○', 'ハ◯レ◯', 'ハ◯撮◯', 'ハ⚪レ⚪', 'ハ⚪撮⚪', 'ハ✗レ✗', 'ハ✗撮✗', 'バOアOラ', 'バOュOムOェO', 'バXアXラ', 'バXュXムXェX', 'バoアoラ', 'バoュoムoェo', 'バxアxラ', 'バxュxムxェx', 'バ■ア■ラ', 'バ■ュ■ム■ェ■', 'バ□ア□ラ', 'バ□ュ□ム□ェ□', 'バ○ア○ラ', 'バ○ュ○ム○ェ○', 'バ◯ア◯ラ', 'バ◯ュ◯ム◯ェ◯', 'バ⚪ア⚪ラ', 'バ⚪ュ⚪ム⚪ェ⚪', 'バ✗ア✗ラ', 'バ✗ュ✗ム✗ェ✗', 'パOズO', 'パOチO', 'パOパO', 'パO活', 'パXズX', 'パXチX', 'パXパX', 'パX活', 'パoズo', 'パoチo', 'パoパo', 'パo活', 'パxズx', 'パxチx', 'パxパx', 'パx活', 'パ■ズ■', 'パ■チ■', 'パ■パ■', 'パ■活', 'パ□ズ□', 'パ□チ□', 'パ□パ□', 'パ□活', 'パ○ズ○', 'パ○チ○', 'パ○パ○', 'パ○活', 'パ◯ズ◯', 'パ◯チ◯', 'パ◯パ◯', 'パ◯活', 'パ⚪ズ⚪', 'パ⚪チ⚪', 'パ⚪パ⚪', 'パ⚪活', 'パ✗ズ✗', 'パ✗チ✗', 'パ✗パ✗', 'パ✗活', 'ビOチ', 'ビXチ', 'ビoチ', 'ビxチ', 'ビ■チ', 'ビ□チ', 'ビ○チ', 'ビ◯チ', 'ビ⚪チ', 'ビ✗チ', 'フOスOフOッO', 'フOラ', 'フOラOき', 'フOラOオ', 'フXスXフXッX', 'フXラ', 'フXラXき', 'フXラXオ', 'フoスoフoッo', 'フoラ', 'フoラoき', 'フoラoオ', 'フxスxフxッx', 'フxラ', 'フxラxき', 'フxラxオ', 'フ■ス■フ■ッ■', 'フ■ラ', 'フ■ラ■き', 'フ■ラ■オ', 'フ□ス□フ□ッ□', 'フ□ラ', 'フ□ラ□き', 'フ□ラ□オ', 'フ○ス○フ○ッ○', 'フ○ラ', 'フ○ラ○き', 'フ○ラ○オ', 'フ◯ス◯フ◯ッ◯', 'フ◯ラ', 'フ◯ラ◯き', 'フ◯ラ◯オ', 'フ⚪ス⚪フ⚪ッ⚪', 'フ⚪ラ', 'フ⚪ラ⚪き', 'フ⚪ラ⚪オ', 'フ✗ス✗フ✗ッ✗', 'フ✗ラ', 'フ✗ラ✗き', 'フ✗ラ✗オ', 'ブOセO', 'ブXセX', 'ブoセo', 'ブxセx', 'ブ■セ■', 'ブ□セ□', 'ブ○セ○', 'ブ◯セ◯', 'ブ⚪セ⚪', 'ブ✗セ✗', 'ペOテOンO', 'ペOバO', 'ペXテXンX', 'ペXバX', 'ペoテoンo', 'ペoバo', 'ペxテxンx', 'ペxバx', 'ペ■テ■ン■', 'ペ■バ■', 'ペ□テ□ン□', 'ペ□バ□', 'ペ○テ○ン○', 'ペ○バ○', 'ペ◯テ◯ン◯', 'ペ◯バ◯', 'ペ⚪テ⚪ン⚪', 'ペ⚪バ⚪', 'ペ✗テ✗ン✗', 'ペ✗バ✗', 'ホO', 'ホX', 'ホo', 'ホx', 'ホ■', 'ホ□', 'ホ○', 'ホ◯', 'ホ⚪', 'ホ✗', 'ボO腹', 'ボX腹', 'ボo腹', 'ボx腹', 'ボ■腹', 'ボ□腹', 'ボ○腹', 'ボ◯腹', 'ボ⚪腹', 'ボ✗腹', 'ポOチO', 'ポXチX', 'ポoチo', 'ポxチx', 'ポ■チ■', 'ポ□チ□', 'ポ○チ○', 'ポ◯チ◯', 'ポ⚪チ⚪', 'ポ✗チ✗', 'マOコ', 'マOタOベOシOン', 'マXコ', 'マXタXベXシXン', 'マoコ', 'マoタoベoシoン', 'マxコ', 'マxタxベxシxン', 'マ■コ', 'マ■タ■ベ■シ■ン', 'マ□コ', 'マ□タ□ベ□シ□ン', 'マ○コ', 'マ○タ○ベ○シ○ン', 'マ◯コ', 'マ◯タ◯ベ◯シ◯ン', 'マ⚪コ', 'マ⚪タ⚪ベ⚪シ⚪ン', 'マ✗コ', 'マ✗タ✗ベ✗シ✗ン', 'ムOムO', 'ムXムX', 'ムoムo', 'ムxムx', 'ム■ム■', 'ム□ム□', 'ム○ム○', 'ム◯ム◯', 'ム⚪ム⚪', 'ム✗ム✗', 'ヤOチO', 'ヤOマO', 'ヤXチX', 'ヤXマX', 'ヤoチo', 'ヤoマo', 'ヤxチx', 'ヤxマx', 'ヤ■チ■', 'ヤ■マ■', 'ヤ□チ□', 'ヤ□マ□', 'ヤ○チ○', 'ヤ○マ○', 'ヤ◯チ◯', 'ヤ◯マ◯', 'ヤ⚪チ⚪', 'ヤ⚪マ⚪', 'ヤ✗チ✗', 'ヤ✗マ✗', 'ラOドOル', 'ラOホ', 'ラOホOル', 'ラXドXル', 'ラXホ', 'ラXホXル', 'ラoドoル', 'ラoホ', 'ラoホoル', 'ラxドxル', 'ラxホ', 'ラxホxル', 'ラ■ド■ル', 'ラ■ホ', 'ラ■ホ■ル', 'ラ□ド□ル', 'ラ□ホ', 'ラ□ホ□ル', 'ラ○ド○ル', 'ラ○ホ', 'ラ○ホ○ル', 'ラ◯ド◯ル', 'ラ◯ホ', 'ラ◯ホ◯ル', 'ラ⚪ド⚪ル', 'ラ⚪ホ', 'ラ⚪ホ⚪ル', 'ラ✗ド✗ル', 'ラ✗ホ', 'ラ✗ホ✗ル', 'リOレ', 'リXレ', 'リoレ', 'リxレ', 'リ■レ', 'リ□レ', 'リ○レ', 'リ◯レ', 'リ⚪レ', 'リ✗レ', 'レOプ', 'レXプ', 'レoプ', 'レxプ', 'レ■プ', 'レ□プ', 'レ○プ', 'レ◯プ', 'レ⚪プ', 'レ✗プ', 'ロOコO', 'ロXコX', 'ロoコo', 'ロxコx', 'ロ■コ■', 'ロ□コ□', 'ロ○コ○', 'ロ◯コ◯', 'ロ⚪コ⚪', 'ロ✗コ✗', '一OＨ', '一XＨ', '一oＨ', '一xＨ', '一■Ｈ', '一□Ｈ', '一○Ｈ', '一◯Ｈ', '一⚪Ｈ', '一✗Ｈ', '中Oし', '中Xし', '中oし', '中xし', '中■し', '中□し', '中○し', '中◯し', '中⚪し', '中✗し', '乙O', '乙X', '乙o', '乙x', '乙■', '乙□', '乙○', '乙◯', '乙⚪', '乙✗', '乱O', '乱O牡O', '乱X', '乱X牡X', '乱o', '乱o牡o', '乱x', '乱x牡x', '乱■', '乱■牡■', '乱□', '乱□牡□', '乱○', '乱○牡○', '乱◯', '乱◯牡◯', '乱⚪', '乱⚪牡⚪', '乱✗', '乱✗牡✗', '乳O', '乳X', '乳o', '乳x', '乳■', '乳□', '乳○', '乳◯', '乳⚪', '乳✗', '亀O', '亀O縛O', '亀X', '亀X縛X', '亀o', '亀o縛o', '亀x', '亀x縛x', '亀■', '亀■縛■', '亀□', '亀□縛□', '亀○', '亀○縛○', '亀◯', '亀◯縛◯', '亀⚪', '亀⚪縛⚪', '亀✗', '亀✗縛✗', '二O', '二O同O', '二X', '二X同X', '二o', '二o同o', '二x', '二x同x', '二■', '二■同■', '二□', '二□同□', '二○', '二○同○', '二◯', '二◯同◯', '二⚪', '二⚪同⚪', '二✗', '二✗同✗', '仮O包O', '仮X包X', '仮o包o', '仮x包x', '仮■包■', '仮□包□', '仮○包○', '仮◯包◯', '仮⚪包⚪', '仮✗包✗', '体O', '体X', '体o', '体x', '体■', '体□', '体○', '体◯', '体⚪', '体✗', '個O撮O', '個X撮X', '個o撮o', '個x撮x', '個■撮■', '個□撮□', '個○撮○', '個◯撮◯', '個⚪撮⚪', '個✗撮✗', '催O', '催X', '催o', '催x', '催■', '催□', '催○', '催◯', '催⚪', '催✗', '兜OわO', '兜XわX', '兜oわo', '兜xわx', '兜■わ■', '兜□わ□', '兜○わ○', '兜◯わ◯', '兜⚪わ⚪', '兜✗わ✗', '入O本O', '入X本X', '入o本o', '入x本x', '入■本■', '入□本□', '入○本○', '入◯本◯', '入⚪本⚪', '入✗本✗', '円O', '円X', '円o', '円x', '円■', '円□', '円○', '円◯', '円⚪', '円✗', '処O', '処X', '処o', '処x', '処■', '処□', '処○', '処◯', '処⚪', '処✗', '包O', '包X', '包o', '包x', '包■', '包□', '包○', '包◯', '包⚪', '包✗', '口O射O', '口O発O', '口X射X', '口X発X', '口o射o', '口o発o', '口x射x', '口x発x', '口■射■', '口■発■', '口□射□', '口□発□', '口○射○', '口○発○', '口◯射◯', '口◯発◯', '口⚪射⚪', '口⚪発⚪', '口✗射✗', '口✗発✗', '唐O居O臼', '唐X居X臼', '唐o居o臼', '唐x居x臼', '唐■居■臼', '唐□居□臼', '唐○居○臼', '唐◯居◯臼', '唐⚪居⚪臼', '唐✗居✗臼', '喘O声', '喘X声', '喘o声', '喘x声', '喘■声', '喘□声', '喘○声', '喘◯声', '喘⚪声', '喘✗声', '四O八O', '四X八X', '四o八o', '四x八x', '四■八■', '四□八□', '四○八○', '四◯八◯', '四⚪八⚪', '四✗八✗', '太OもOキ', '太XもXキ', '太oもoキ', '太xもxキ', '太■も■キ', '太□も□キ', '太○も○キ', '太◯も◯キ', '太⚪も⚪キ', '太✗も✗キ', '姫Oめ', '姫Xめ', '姫oめ', '姫xめ', '姫■め', '姫□め', '姫○め', '姫◯め', '姫⚪め', '姫✗め', '媚O', '媚X', '媚o', '媚x', '媚■', '媚□', '媚○', '媚◯', '媚⚪', '媚✗', '孕Oせ', '孕Xせ', '孕oせ', '孕xせ', '孕■せ', '孕□せ', '孕○せ', '孕◯せ', '孕⚪せ', '孕✗せ', '寝OらO', '寝Oり', '寝XらX', '寝Xり', '寝oらo', '寝oり', '寝xらx', '寝xり', '寝■ら■', '寝■り', '寝□ら□', '寝□り', '寝○ら○', '寝○り', '寝◯ら◯', '寝◯り', '寝⚪ら⚪', '寝⚪り', '寝✗ら✗', '寝✗り', '寿O手', '寿X手', '寿o手', '寿x手', '寿■手', '寿□手', '寿○手', '寿◯手', '寿⚪手', '寿✗手', '射O', '射X', '射o', '射x', '射■', '射□', '射○', '射◯', '射⚪', '射✗', '屍O', '屍X', '屍o', '屍x', '屍■', '屍□', '屍○', '屍◯', '屍⚪', '屍✗', '巨O', '巨X', '巨o', '巨x', '巨■', '巨□', '巨○', '巨◯', '巨⚪', '巨✗', '帆OけO臼', '帆XけX臼', '帆oけo臼', '帆xけx臼', '帆■け■臼', '帆□け□臼', '帆○け○臼', '帆◯け◯臼', '帆⚪け⚪臼', '帆✗け✗臼', '座O', '座X', '座o', '座x', '座■', '座□', '座○', '座◯', '座⚪', '座✗', '強O', '強X', '強o', '強x', '強■', '強□', '強○', '強◯', '強⚪', '強✗', '後O位', '後X位', '後o位', '後x位', '後■位', '後□位', '後○位', '後◯位', '後⚪位', '後✗位', '微O', '微X', '微o', '微x', '微■', '微□', '微○', '微◯', '微⚪', '微✗', '忍O居O臼', '忍X居X臼', '忍o居o臼', '忍x居x臼', '忍■居■臼', '忍□居□臼', '忍○居○臼', '忍◯居◯臼', '忍⚪居⚪臼', '忍✗居✗臼', '快O堕O', '快X堕X', '快o堕o', '快x堕x', '快■堕■', '快□堕□', '快○堕○', '快◯堕◯', '快⚪堕⚪', '快✗堕✗', '性O', '性OマOサOジ', '性O帯', '性O為', '性O理', '性O隷', '性X', '性XマXサXジ', '性X帯', '性X為', '性X理', '性X隷', '性o', '性oマoサoジ', '性o帯', '性o為', '性o理', '性o隷', '性x', '性xマxサxジ', '性x帯', '性x為', '性x理', '性x隷', '性■', '性■マ■サ■ジ', '性■帯', '性■為', '性■理', '性■隷', '性□', '性□マ□サ□ジ', '性□帯', '性□為', '性□理', '性□隷', '性○', '性○マ○サ○ジ', '性○帯', '性○為', '性○理', '性○隷', '性◯', '性◯マ◯サ◯ジ', '性◯帯', '性◯為', '性◯理', '性◯隷', '性⚪', '性⚪マ⚪サ⚪ジ', '性⚪帯', '性⚪為', '性⚪理', '性⚪隷', '性✗', '性✗マ✗サ✗ジ', '性✗帯', '性✗為', '性✗理', '性✗隷', '愛O', '愛X', '愛o', '愛x', '愛■', '愛□', '愛○', '愛◯', '愛⚪', '愛✗', '成O向O', '成X向X', '成o向o', '成x向x', '成■向■', '成□向□', '成○向○', '成◯向◯', '成⚪向⚪', '成✗向✗', '我O汁', '我X汁', '我o汁', '我x汁', '我■汁', '我□汁', '我○汁', '我◯汁', '我⚪汁', '我✗汁', '手O', '手Oキ', '手Oン', '手X', '手Xキ', '手Xン', '手o', '手oキ', '手oン', '手x', '手xキ', '手xン', '手■', '手■キ', '手■ン', '手□', '手□キ', '手□ン', '手○', '手○キ', '手○ン', '手◯', '手◯キ', '手◯ン', '手⚪', '手⚪キ', '手⚪ン', '手✗', '手✗キ', '手✗ン', '抱O地O', '抱X地X', '抱o地o', '抱x地x', '抱■地■', '抱□地□', '抱○地○', '抱◯地◯', '抱⚪地⚪', '抱✗地✗', '揚O本O', '揚X本X', '揚o本o', '揚x本x', '揚■本■', '揚□本□', '揚○本○', '揚◯本◯', '揚⚪本⚪', '揚✗本✗', '援O', '援O交O', '援X', '援X交X', '援o', '援o交o', '援x', '援x交x', '援■', '援■交■', '援□', '援□交□', '援○', '援○交○', '援◯', '援◯交◯', '援⚪', '援⚪交⚪', '援✗', '援✗交✗', '放O', '放OプOイ', '放X', '放XプXイ', '放o', '放oプoイ', '放x', '放xプxイ', '放■', '放■プ■イ', '放□', '放□プ□イ', '放○', '放○プ○イ', '放◯', '放◯プ◯イ', '放⚪', '放⚪プ⚪イ', '放✗', '放✗プ✗イ', '早O', '早X', '早o', '早x', '早■', '早□', '早○', '早◯', '早⚪', '早✗', '時O茶O', '時X茶X', '時o茶o', '時x茶x', '時■茶■', '時□茶□', '時○茶○', '時◯茶◯', '時⚪茶⚪', '時✗茶✗', '月O茶O', '月X茶X', '月o茶o', '月x茶x', '月■茶■', '月□茶□', '月○茶○', '月◯茶◯', '月⚪茶⚪', '月✗茶✗', '朝Oち', '朝Xち', '朝oち', '朝xち', '朝■ち', '朝□ち', '朝○ち', '朝◯ち', '朝⚪ち', '朝✗ち', '松O崩O', '松X崩X', '松o崩o', '松x崩x', '松■崩■', '松□崩□', '松○崩○', '松◯崩◯', '松⚪崩⚪', '松✗崩✗', '機O茶O', '機X茶X', '機o茶o', '機x茶x', '機■茶■', '機□茶□', '機○茶○', '機◯茶◯', '機⚪茶⚪', '機✗茶✗', '正O位', '正X位', '正o位', '正x位', '正■位', '正□位', '正○位', '正◯位', '正⚪位', '正✗位', '汁O優', '汁X優', '汁o優', '汁x優', '汁■優', '汁□優', '汁○優', '汁◯優', '汁⚪優', '汁✗優', '泡O', '泡X', '泡o', '泡x', '泡■', '泡□', '泡○', '泡◯', '泡⚪', '泡✗', '洞OりO手', '洞XりX手', '洞oりo手', '洞xりx手', '洞■り■手', '洞□り□手', '洞○り○手', '洞◯り◯手', '洞⚪り⚪手', '洞✗り✗手', '淫O', '淫X', '淫o', '淫x', '淫■', '淫□', '淫○', '淫◯', '淫⚪', '淫✗', '熟O', '熟X', '熟o', '熟x', '熟■', '熟□', '熟○', '熟◯', '熟⚪', '熟✗', '爆O', '爆X', '爆o', '爆x', '爆■', '爆□', '爆○', '爆◯', '爆⚪', '爆✗', '獣O', '獣X', '獣o', '獣x', '獣■', '獣□', '獣○', '獣◯', '獣⚪', '獣✗', '玉Oめ', '玉Xめ', '玉oめ', '玉xめ', '玉■め', '玉□め', '玉○め', '玉◯め', '玉⚪め', '玉✗め', '生Oメ', '生Xメ', '生oメ', '生xメ', '生■メ', '生□メ', '生○メ', '生◯メ', '生⚪メ', '生✗メ', '男O', '男X', '男o', '男x', '男■', '男□', '男○', '男◯', '男⚪', '男✗', '痴O', '痴X', '痴o', '痴x', '痴■', '痴□', '痴○', '痴◯', '痴⚪', '痴✗', '発O', '発X', '発o', '発x', '発■', '発□', '発○', '発◯', '発⚪', '発✗', '真O包O', '真X包X', '真o包o', '真x包x', '真■包■', '真□包□', '真○包○', '真◯包◯', '真⚪包⚪', '真✗包✗', '睡O', '睡X', '睡o', '睡x', '睡■', '睡□', '睡○', '睡◯', '睡⚪', '睡✗', '睾O', '睾X', '睾o', '睾x', '睾■', '睾□', '睾○', '睾◯', '睾⚪', '睾✗', '種Oけ', '種OけOレO', '種Xけ', '種XけXレX', '種oけ', '種oけoレo', '種xけ', '種xけxレx', '種■け', '種■け■レ■', '種□け', '種□け□レ□', '種○け', '種○け○レ○', '種◯け', '種◯け◯レ◯', '種⚪け', '種⚪け⚪レ⚪', '種✗け', '種✗け✗レ✗', '穴O弟', '穴X弟', '穴o弟', '穴x弟', '穴■弟', '穴□弟', '穴○弟', '穴◯弟', '穴⚪弟', '穴✗弟', '立OんO', '立XんX', '立oんo', '立xんx', '立■ん■', '立□ん□', '立○ん○', '立◯ん◯', '立⚪ん⚪', '立✗ん✗', '童O', '童X', '童o', '童x', '童■', '童□', '童○', '童◯', '童⚪', '童✗', '笠O本O', '笠X本X', '笠o本o', '笠x本x', '笠■本■', '笠□本□', '笠○本○', '笠◯本◯', '笠⚪本⚪', '笠✗本✗', '筆OろO', '筆XろX', '筆oろo', '筆xろx', '筆■ろ■', '筆□ろ□', '筆○ろ○', '筆◯ろ◯', '筆⚪ろ⚪', '筆✗ろ✗', '筏O手', '筏X手', '筏o手', '筏x手', '筏■手', '筏□手', '筏○手', '筏◯手', '筏⚪手', '筏✗手', '粗Oン', '粗Xン', '粗oン', '粗xン', '粗■ン', '粗□ン', '粗○ン', '粗◯ン', '粗⚪ン', '粗✗ン', '素O', '素O ', '素X', '素X ', '素o', '素o ', '素x', '素x ', '素■', '素■ ', '素□', '素□ ', '素○', '素○ ', '素◯', '素◯ ', '素⚪', '素⚪ ', '素✗', '素✗ ', '絶O', '絶X', '絶o', '絶x', '絶■', '絶□', '絶○', '絶◯', '絶⚪', '絶✗', '網O本O', '網X本X', '網o本o', '網x本x', '網■本■', '網□本□', '網○本○', '網◯本◯', '網⚪本⚪', '網✗本✗', '緊O', '緊X', '緊o', '緊x', '緊■', '緊□', '緊○', '緊◯', '緊⚪', '緊✗', '肉O器', '肉X器', '肉o器', '肉x器', '肉■器', '肉□器', '肉○器', '肉◯器', '肉⚪器', '肉✗器', '胸Oラ', '胸Xラ', '胸oラ', '胸xラ', '胸■ラ', '胸□ラ', '胸○ラ', '胸◯ラ', '胸⚪ラ', '胸✗ラ', '脇Oキ', '脇Xキ', '脇oキ', '脇xキ', '脇■キ', '脇□キ', '脇○キ', '脇◯キ', '脇⚪キ', '脇✗キ', '自O', '自X', '自o', '自x', '自■', '自□', '自○', '自◯', '自⚪', '自✗', '菊O', '菊X', '菊o', '菊x', '菊■', '菊□', '菊○', '菊◯', '菊⚪', '菊✗', '蟻O戸Oり', '蟻X戸Xり', '蟻o戸oり', '蟻x戸xり', '蟻■戸■り', '蟻□戸□り', '蟻○戸○り', '蟻◯戸◯り', '蟻⚪戸⚪り', '蟻✗戸✗り', '裏O', '裏X', '裏o', '裏x', '裏■', '裏□', '裏○', '裏◯', '裏⚪', '裏✗', '貝OわO', '貝XわX', '貝oわo', '貝xわx', '貝■わ■', '貝□わ□', '貝○わ○', '貝◯わ◯', '貝⚪わ⚪', '貝✗わ✗', '貧O', '貧X', '貧o', '貧x', '貧■', '貧□', '貧○', '貧◯', '貧⚪', '貧✗', '足Oキ', '足Xキ', '足oキ', '足xキ', '足■キ', '足□キ', '足○キ', '足◯キ', '足⚪キ', '足✗キ', '輪O', '輪X', '輪o', '輪x', '輪■', '輪□', '輪○', '輪◯', '輪⚪', '輪✗', '近O相O', '近X相X', '近o相o', '近x相x', '近■相■', '近□相□', '近○相○', '近◯相◯', '近⚪相⚪', '近✗相✗', '逆OイO', '逆OナO', '逆XイX', '逆XナX', '逆oイo', '逆oナo', '逆xイx', '逆xナx', '逆■イ■', '逆■ナ■', '逆□イ□', '逆□ナ□', '逆○イ○', '逆○ナ○', '逆◯イ◯', '逆◯ナ◯', '逆⚪イ⚪', '逆⚪ナ⚪', '逆✗イ✗', '逆✗ナ✗', '遅O', '遅X', '遅o', '遅x', '遅■', '遅□', '遅○', '遅◯', '遅⚪', '遅✗', '金O', '金X', '金o', '金x', '金■', '金□', '金○', '金◯', '金⚪', '金✗', '陰O', '陰X', '陰o', '陰x', '陰■', '陰□', '陰○', '陰◯', '陰⚪', '陰✗', '陵O', '陵X', '陵o', '陵x', '陵■', '陵□', '陵○', '陵◯', '陵⚪', '陵✗', '雁O首', '雁X首', '雁o首', '雁x首', '雁■首', '雁□首', '雁○首', '雁◯首', '雁⚪首', '雁✗首', '電O', '電X', '電o', '電x', '電■', '電□', '電○', '電◯', '電⚪', '電✗', '青O', '青X', '青o', '青x', '青■', '青□', '青○', '青◯', '青⚪', '青✗', '顔O', '顔X', '顔o', '顔x', '顔■', '顔□', '顔○', '顔◯', '顔⚪', '顔✗', '食O', '食X', '食o', '食x', '食■', '食□', '食○', '食◯', '食⚪', '食✗', '飲O', '飲X', '飲o', '飲x', '飲■', '飲□', '飲○', '飲◯', '飲⚪', '飲✗', '首OきO慕', '首XきX慕', '首oきo慕', '首xきx慕', '首■き■慕', '首□き□慕', '首○き○慕', '首◯き◯慕', '首⚪き⚪慕', '首✗き✗慕', '騎O位', '騎X位', '騎o位', '騎x位', '騎■位', '騎□位', '騎○位', '騎◯位', '騎⚪位', '騎✗位', '鶯O谷Oり', '鶯X谷Xり', '鶯o谷oり', '鶯x谷xり', '鶯■谷■り', '鶯□谷□り', '鶯○谷○り', '鶯◯谷◯り', '鶯⚪谷⚪り', '鶯✗谷✗り', '黄O水', '黄X水', '黄o水', '黄x水', '黄■水', '黄□水', '黄○水', '黄◯水', '黄⚪水', '黄✗水', '黒OャO', '黒XャX', '黒oャo', '黒xャx', '黒■ャ■', '黒□ャ□', '黒○ャ○', '黒◯ャ◯', '黒⚪ャ⚪', '黒✗ャ✗', 'ＳOプOイ', 'ＳXプXイ', 'Ｓoプoイ', 'Ｓxプxイ', 'Ｓ■プ■イ', 'Ｓ□プ□イ', 'Ｓ○プ○イ', 'Ｓ◯プ◯イ', 'Ｓ⚪プ⚪イ', 'Ｓ✗プ✗イ', 'ﾁOﾁO', 'ﾁXﾁX', 'ﾁoﾁo', 'ﾁxﾁx', 'ﾁ■ﾁ■', 'ﾁ□ﾁ□', 'ﾁ○ﾁ○', 'ﾁ◯ﾁ◯', 'ﾁ⚪ﾁ⚪', 'ﾁ✗ﾁ✗']

        async def contains_banned_word_async(text: str) -> bool:
            normalized_text = neologdn.normalize(text)
            all_banned_words = banned_words + banned_words2
            return any(word in normalized_text for word in all_banned_words)

        if await contains_banned_word_async(self.codeinput.value):
            return await interaction.followup.send("予期しないエラーが発生しました。", ephemeral=True)
        
        try:
            container = interaction.client.container(interaction.client)
            label = "ボタンのラベル"

            for c in self.codeinput.value.split("\n"):
                if c.startswith("text:"):
                    container.add_view(container.text(c.removeprefix("text:")))
                elif c.startswith("line:"):
                    container.add_view(container.separator())
                elif c.startswith("action:"):
                    container.add_view(container.action_row())
                elif c.startswith("url:"):
                    container.add_view(container.labeled_button(label, container.labeled_link("アクセス", c.removeprefix("url:"))))
                elif c.startswith("label:"):
                    label = c.removeprefix("label:")
                else:
                    container.add_view(container.text(c))

            container.add_view(container.text(f"作成者: {interaction.user.name}"))

            color = discord.Color.from_str(self.color.value)

            j = await container.send(color.__int__(), interaction.channel.id)
            return await interaction.followup.send(f"作成しました。", ephemeral=True)

        except Exception as e:
            return await interaction.followup.send(f"予期しないエラーが発生しました。", ephemeral=True)

domain_regex = re.compile(
    r"^(?!\-)(?:[a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$"
)

async def fetch_whois(target_domain):
    if not domain_regex.match(target_domain):
        return io.StringIO("Whoisに失敗しました。")
    def whois_query(domain: str, server="whois.iana.org") -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server, 43))
            s.sendall((domain + "\r\n").encode())
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            return response.decode(errors="ignore")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, partial(whois_query, target_domain))
    return io.StringIO(res)

async def ping_domein(domein: str, port: int):
    try:
        data = {
            'params': f'target_domain={urllib.parse.quote_plus(domein)}&target_port={port}',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://tech-unlimited.com/proc/ping.php", data=data) as response:
                if response.status == 200:
                    return json.loads(await response.text())
                else:
                    return None
    except Exception as e:
        return None

ipv4_pattern = re.compile(
    r'^('
    r'(25[0-5]|'        # 250-255
    r'2[0-4][0-9]|'     # 200-249
    r'1[0-9]{2}|'       # 100-199
    r'[1-9][0-9]|'      # 10-99
    r'[0-9])'           # 0-9
    r'\.){3}'           # 繰り返し: 3回ドット付き
    r'(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'  # 最後のオクテット
    r'$'
)

class Calculator(discord.ui.View):
    def __init__(self):
        self.calculator = "0"
        super().__init__(timeout=None)

    @discord.ui.button(label="0", style=discord.ButtonStyle.blurple, row=0)
    async def _0(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "0"
        else:
            self.calculator += "0"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.blurple, row=0)
    async def _1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "1"
        else:
            self.calculator += "1"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="2", style=discord.ButtonStyle.blurple, row=0)
    async def _2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "2"
        else:
            self.calculator += "2"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="3", style=discord.ButtonStyle.blurple, row=0)
    async def _3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "3"
        else:
            self.calculator += "3"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="4", style=discord.ButtonStyle.blurple, row=1)
    async def _4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "4"
        else:
            self.calculator += "4"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="5", style=discord.ButtonStyle.blurple, row=1)
    async def _5(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "5"
        else:
            self.calculator += "5"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="6", style=discord.ButtonStyle.blurple, row=1)
    async def _6(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "6"
        else:
            self.calculator += "6"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="7", style=discord.ButtonStyle.blurple, row=1)
    async def _7(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "7"
        else:
            self.calculator += "7"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="8", style=discord.ButtonStyle.blurple, row=2)
    async def _8(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "8"
        else:
            self.calculator += "8"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="9", style=discord.ButtonStyle.blurple, row=2)
    async def _9(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "9"
        else:
            self.calculator += "9"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="10", style=discord.ButtonStyle.blurple, row=2)
    async def _10(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "10"
        else:
            self.calculator += "10"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="100", style=discord.ButtonStyle.blurple, row=2)
    async def _100(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "100"
        else:
            self.calculator += "100"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="+", style=discord.ButtonStyle.blurple, row=3)
    async def _plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "+"
        else:
            self.calculator += "+"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="-", style=discord.ButtonStyle.blurple, row=3)
    async def _minus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.calculator == "0":
            self.calculator = "-"
        else:
            self.calculator += "-"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="=", style=discord.ButtonStyle.green, row=3)
    async def _equals(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if self.calculator == "0":
            return
        
        def safe_calculator(expression: str):
            expression = expression.replace(" ", "")
            
            def check_number(n):
                if abs(n) > 10000:
                    return 0
                return n

            def parse_mul_div(tokens):
                result = float(tokens[0])
                i = 1
                while i < len(tokens):
                    op = tokens[i]
                    num = float(tokens[i + 1])
                    if op == '*':
                        result *= num
                    elif op == '/':
                        if num == 0:
                            return "0で割ることはできません。"
                        result /= num
                    i += 2
                return result

            def parse_add_sub(expression):
                tokens = re.findall(r'[+-]?\d+(?:\.\d+)?|[*/]', expression)
                new_tokens = []
                i = 0
                while i < len(tokens):
                    if tokens[i] in '*/':
                        a = new_tokens.pop()
                        op = tokens[i]
                        b = tokens[i + 1]
                        result = parse_mul_div([a, op, b])
                        new_tokens.append(str(result))
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1

                result = check_number(float(new_tokens[0]))
                i = 1
                while i < len(new_tokens):
                    op = new_tokens[i][0]
                    num_str = new_tokens[i][1:] if len(new_tokens[i]) > 1 else new_tokens[i + 1]
                    num = check_number(float(num_str))
                    if op == '+':
                        result = check_number(result + num)
                    elif op == '-':
                        result = check_number(result - num)
                    i += 1 if len(new_tokens[i]) > 1 else 2
                return result

            try:
                return parse_add_sub(expression)
            except Exception as e:
                return f"エラー！"

        result = safe_calculator(self.calculator)
        self.calculator = f"{result}"
        await interaction.message.edit(content=f"{result}", view=self)

    @discord.ui.button(label="C", style=discord.ButtonStyle.red, row=3)
    async def _C(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.calculator = "0"
        await interaction.message.edit(content=self.calculator, view=self)

    @discord.ui.button(label="10000以上は計算できません。", style=discord.ButtonStyle.gray, row=4, disabled=True)
    async def _keikoku(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.calculator = "0"
        await interaction.response.edit_message(content=self.calculator, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.red, row=4)
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(content=self.calculator, view=None)
        await interaction.response.send_message("計算機を終了しました。", ephemeral=True)

cooldown_afk = {}
cooldown_sh_command = {}

class ToolCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ToolCog")

    async def get_bothyoka(self, bot: discord.User):
        db = self.bot.async_db["Main"].BotHyokaBun
        try:
            dbfind = await db.find_one({"Bot": f"{bot.id}"}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind["Content"] + "\n" + "著者: " + self.bot.get_user(dbfind["User"]).display_name

    def is_valid_url(self, url):
        url_regex = re.compile(
            r'https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(url_regex, url) is not None

    async def afk_mention_get(self, user: discord.User):
        try:
            database = self.bot.async_db["Main"].AFKMention
            m = [f"{self.bot.get_channel(b.get("Channel", 0)).mention if self.bot.get_channel(b.get("Channel", 0)) else b.get("Channel", 0)} - {self.bot.get_user(b.get('MentionUser')) if self.bot.get_user(b.get('MentionUser')) else b.get('MentionUser')}" async for b in database.find({"User": user.id})]
            await database.delete_many({
                "User": user.id,
            })
            return "\n".join(m)
        except Exception as e:
            return f"取得失敗！\n{e}"

    @commands.Cog.listener("on_message")
    async def on_message_afk(self, message: discord.Message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].AFK
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        mens = await self.afk_mention_get(message.author)
        if mens == "":
            mens = "メンションなし"
        try:
            await message.reply(embed=discord.Embed(title="AFKを解除しました。", description=f"{dbfind["Reason"]}", color=discord.Color.green()).add_field(name="今から何する？", value=dbfind.get("End", "まだ予定がありません。"), inline=False).add_field(name="メンション一覧", value=mens, inline=False))
        except:
            pass
        await db.delete_one({
            "User": message.author.id,
        })

    @commands.Cog.listener("on_message")
    async def on_message_afk_post(self, message):
        if message.channel.id == 1329969245362327582:
            try:
                content = message.content.split(",")
                author = content[0]
                reason = content[1]
                db = self.bot.async_db["Main"].AFK
                await db.replace_one(
                    {"User": int(author)}, 
                    {"User": int(author), "Reason": reason}, 
                    upsert=True
                )
            except:
                return

    async def afk_mention_write(self, user: int, message: discord.Message):
        database = self.bot.async_db["Main"].AFKMention
        await database.replace_one(
            {"User": user, "Channel": message.channel.id, "MentionUser": message.author.id}, 
            {"User": user, "MentionUser": message.author.id, "Channel": message.channel.id}, 
            upsert=True
        )

    @commands.Cog.listener("on_message")
    async def on_message_afk_mention(self, message):
        if message.author.bot:
            return
        if message.mentions:
            mentioned_users = [user.id for user in message.mentions]
            for m in mentioned_users:
                db = self.bot.async_db["Main"].AFK
                try:
                    dbfind = await db.find_one({"User": m}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_afk.get(message.author.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_afk[message.author.id] = current_time
                await self.afk_mention_write(m, message)
                await message.reply(embed=discord.Embed(title=f"その人はAFKです。", description=f"理由: {dbfind["Reason"]}", color=discord.Color.red()).set_footer(text="このメッセージを5秒後に削除されます。"), delete_after=5)
                return

    async def user_block_command(self, message: discord.Message):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return False
        if not dbfind is None:
            return True
        return False
    
    async def block_check(self, user: discord.User):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return False
        if not dbfind is None:
            return True
        return False

    @commands.Cog.listener("on_message")
    async def on_message_secound_command(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content.strip():
            return

        if message.content.startswith("sh:"):
            check = await self.user_block_command(message)
            if check:
                return
            current_time = time.time()
            last_message_time = cooldown_sh_command.get(message.author.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_sh_command[message.author.id] = current_time
            try:
                command = message.content.split("sh:")[1].split(" ")[0]
                args = message.content.split(f" ")
                if command == "dpy":
                    if not len(args) == 2:
                        return
                    await message.add_reaction("🔍")
                    async with aiofiles.open("Document/discord-py.html", mode='r', encoding="utf-8") as f:
                        content = await f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    title = soup.find_all('a', {'class', "headerlink"})
                    ti = []
                    for t in title:
                        if re.search(f"{args[1]}", t["href"]):
                            ti.append(f"[{t["href"]}](https://discordpy.readthedocs.io/ja/latest/api.html{t["href"]})")
                    ttt = ti[:10]
                    if len(ttt) == 0:
                        await message.add_reaction("❌")
                        return
                    await message.reply("\n".join(ttt))
                if command == "mute":
                    if not len(args) == 2:
                        return
                    await message.add_reaction("🔍")
                    try:
                        id = int(args[1])
                        user = await self.bot.fetch_user(id)
                    except:
                        return
                    us = await self.block_check(user)
                    if not us:
                        return await message.reply("Muted? No.")
                    if us:
                        return await message.reply("Muted? Yes.")
            except:
                await message.add_reaction("‼️")
                return

    """

    @commands.Cog.listener("on_message")
    async def on_message_detect_selfbot(self, message: discord.Message):
        if message.author.bot:
            return
        prefixs = ["!", "?", ";", "*", "-", "$", "+", ">", ">>", "^", "=", "|"]
        for p in prefixs:
            if message.content.startswith(p):
                original_message_id = message.id

                try:

                    def check(reply_msg):
                        return (
                            reply_msg.reference is not None and
                            reply_msg.reference.message_id == original_message_id and
                            not reply_msg.author.bot
                        )

                    try:
                        reply = await self.bot.wait_for("message", timeout=2, check=check)
                        if reply.bot:
                            return
                        print("セルフボットを検知しました。")
                    except asyncio.TimeoutError:
                        return
                except:
                    return
    """
                    
    @commands.hybrid_group(name="tools", description="AFKを設定します。", fallback="afk")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def afk_set(self, ctx: commands.Context, 理由: str, 終わったらやること: str = "まだ予定がありません。"):
        await ctx.defer()
        database = self.bot.async_db["Main"].AFK
        await database.replace_one(
            {"User": ctx.author.id}, 
            {"User": ctx.author.id, "Reason": 理由, "End": 終わったらやること}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> AFKを設定しました。", description=f"{理由}", color=discord.Color.green()))

    @afk_set.command(name="embed", description="埋め込みを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def embed(self, ctx: commands.Context):
        await ctx.interaction.response.send_modal(RunEmbedMake())

    @afk_set.command(name="container", description="新しいguiの埋め込みを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def container_builder(self, ctx: commands.Context):
        await ctx.interaction.response.send_modal(RunContainerMake())

    @afk_set.command(name="button", description="ボタンを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def button_builder(self, ctx: commands.Context, ラベル: str, url: str = "https://google.com"):
        if not ctx.interaction:
            return await ctx.reply(content="スラッシュコマンドからお願いします。")
        class ButtonBuilder(discord.ui.View):
            def __init__(self, *, timeout = 180):
                super().__init__(timeout=timeout)
                self.roles = []
                    
            @discord.ui.select(
                cls=discord.ui.RoleSelect,
                placeholder="ロールを選択",
                max_values=5,
                min_values=1
            )
            async def role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
                self.roles = select.values
                await interaction.response.send_message(content="ロールを選択しました。", ephemeral=True)

            @discord.ui.button(label="通常送信", style=discord.ButtonStyle.green)
            async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label=ラベル, url=url))
                await interaction.channel.send(view=view, content=f"-# 作成者: {ctx.author.name} ({ctx.author.id})")

            @discord.ui.button(label="ロールをつけて送信", style=discord.ButtonStyle.green)
            async def send_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not interaction.user.guild_permissions.manage_roles:
                    return await interaction.response.send_message(embed=discord.Embed(title="権限がありません。", color=discord.Color.red()), ephemeral=True)
                await interaction.response.defer(ephemeral=True)
                if not self.roles:
                    return await interaction.followup.send(ephemeral=True, content="ロールが見つかりません。")
                view = discord.ui.View()
                for rl in self.roles:
                    view.add_item(discord.ui.Button(label=ラベル, custom_id=f"rolepanel_v1+{rl.id}"))
                await interaction.channel.send(view=view, content=f"-# 作成者: {ctx.author.name} ({ctx.author.id})")
                
        await ctx.reply(view=ButtonBuilder(), ephemeral=True)

    @afk_set.command(name="whois", description="Whois検索をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def whois(self, ctx: commands.Context, ドメイン: str):
        await ctx.defer()
        data = await fetch_whois(ドメイン)
        return await ctx.reply(file=discord.File(data, "whois.txt"))

    @afk_set.command(name="ping", description="ドメインの応答速度を確認します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ping_domein(self, ctx: commands.Context, ドメイン: str, ポート: int = 80):
        msg = await ctx.defer()
        try:
            data = await ping_domein(ドメイン, ポート)
            if data is None:
                return await ctx.reply(embed=discord.Embed(title="タイムアウトしました。", color=discord.Color.red()))
            return await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> ドメインの応答速度", description=f"{data["result"]}\n応答速度: {data["response_time"]}\nポート: {data["port"]}", color=discord.Color.green()))
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title="エラーが発生しました。", description=f"{e}", color=discord.Color.red()))

    @afk_set.command(name="nslookup", description="DNS情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nslookup(self, ctx: commands.Context, ドメイン: str):
        await ctx.defer()
        l = []
        domain = ドメイン
        json_data = {
            'domain': domain,
            'dnsServer': 'cloudflare',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://www.nslookup.io/api/v1/records", json=json_data) as response:
                js = await response.json()
                records_data = js.get("records", {})
                categorized_records = {}

                for record_type, record_info in records_data.items():
                    response = record_info.get("response", {})
                    answers = response.get("answer", [])
                    
                    for answer in answers:
                        record_details = answer.get("record", {})
                        ip_info = answer.get("ipInfo", {})
                        
                        record_entry = (
                            f"{record_details.get('raw', 'N/A')}"
                        )
                        
                        if record_type not in categorized_records:
                            categorized_records[record_type] = []
                        categorized_records[record_type].append(record_entry)

                embed = discord.Embed(title="<:Success:1362271281302601749> NSLookup DNS情報", color=discord.Color.blue())
                
                for record_type, entries in categorized_records.items():
                    value_text = "\n".join(entries)
                    embed.add_field(name=record_type.upper(), value=value_text[:1024], inline=False)

                embed.set_footer(text=domain)
                
                await ctx.send(embed=embed)

    @afk_set.command(name="iplookup", description="IP情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def iplookup(self, ctx: commands.Context, ipアドレス: str):
        if ipv4_pattern.match(ipアドレス):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ipアドレス}?lang=ja") as response:
                    try:
                        js = await response.json()
                        await ctx.reply(embed=discord.Embed(title=f"IPアドレス情報 ({ipアドレス})", description=f"""
    国名: {js.get("country", "不明")}
    都市名: {js.get("city", "不明")}
    プロバイダ: {js.get("isp", "不明")}
    緯度: {js.get("lat", "不明")}
    経度: {js.get("lon", "不明")}
    タイムゾーン: {js.get("timezone", "不明")}
    """, color=discord.Color.green()))
                    except:
                        return await ctx.reply(embed=discord.Embed(title="APIのレートリミットです。", color=discord.Color.red()))
        else:
            return await ctx.reply(embed=discord.Embed(title="無効なIPアドレスです。", color=discord.Color.red()))

    @afk_set.command(name="log", description="チャットログを出力します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def chat_log(self, ctx: commands.Context, チャンネルid: str = None):
        try:
            await ctx.defer(ephemeral=True)
            def randomname(n):
                randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
                return ''.join(randlst)
            ran = randomname(30)
            pas = randomname(10)
            async def save_message(message: discord.Message):
                if message.content == "":
                    msg = "埋め込みがあります。"
                else:
                    def replace_mention_with_id(match):
                        return self.bot.get_user(int(match.group(1))).display_name
                    
                    def replace_mention_with_channel_id(match):
                        return self.bot.get_channel(int(match.group(1))).name
                    msg = re.sub(r"<#(\d+)>", replace_mention_with_channel_id, re.sub(r"<@!?(\d+)>", replace_mention_with_id, message.content))
                try:
                    message_data = {
                        "username": message.author.name,
                        "user_id": str(message.author.id),
                        "timestamp": f"{message.created_at}",
                        "content": msg,
                        "channel_id": str(message.channel.id),
                        "message_id": str(message.id),
                        "avatar_url": message.author.avatar.url if message.author.avatar else message.author.default_avatar.url,
                        "chatid": ran,
                        "password": pas
                    }
                    await self.bot.async_db["Main"].ChatCapture.insert_one(message_data)
                except:
                    pass
            db = self.bot.async_db["Main"].ChatCapture
            if not チャンネルid:
                async for chm in ctx.channel.history(limit=100):
                    await save_message(chm)
                return await ctx.reply(f"ログを出力しました。\n削除パスワード: {pas}\nhttps://www.sharkbot.xyz/capture/{ran}")
            else:
                return await ctx.reply("チャンネルidを指定してください。")
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title="ログを出力できませんでした。", description=f"{e}", color=discord.Color.red()), ephemeral=True)

    @afk_set.command(name='compile', description = "コンパイルします。")
    @app_commands.choices(言語=[
        app_commands.Choice(name='python',value="python"),
        app_commands.Choice(name='nodejs',value="nodejs"),
        app_commands.Choice(name='c++',value="cpp"),
        app_commands.Choice(name='c#',value="csharp"),
    ])
    async def compile_(self, ctx: commands.Context, 言語: app_commands.Choice[str]):
        if 言語.name == "python":
            await ctx.interaction.response.send_modal(RunPython())
        elif 言語.name == "nodejs":
            await ctx.interaction.response.send_modal(RunNodeJS())
        elif 言語.name == "c++":
            await ctx.interaction.response.send_modal(RunCPlapla())
        elif 言語.name == "c#":
            await ctx.interaction.response.send_modal(RunCSharp())

    @afk_set.command(name="auditlog", description="監査ログを出力します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(データ=[
        app_commands.Choice(name='BANログ',value="ban"),
    ])
    @commands.has_permissions(manage_channels=True)
    async def auditlog(self, ctx: commands.Context, データ: app_commands.Choice[str]):
        guild = ctx.guild
        await ctx.defer()
        if データ.value == "ban":
            word = ""
            async for entry in guild.audit_logs(limit=50, action=discord.AuditLogAction.ban):
                word += f"{entry.user} が {entry.target} をBANしました。理由: {entry.reason}\n"
            w = io.StringIO(word)
            await ctx.reply(file=discord.File(w, "log.txt"))

    @afk_set.command(name="uuid", description="UUIDを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def uuid(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.uuidtools.com/api/generate/v1") as response:
                jso = await response.json()
                await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> UUID生成", description=f"{jso[0]}", color=discord.Color.green()))

    @afk_set.command(name="invite", description="サーバーの招待リンクを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(create_instant_invite=True)
    async def invite(self, ctx: commands.Context, 招待url: str = None):
        await ctx.defer()
        if 招待url:
            if not ctx.author.guild_permissions.manage_guild:
                return await ctx.reply(embed=discord.Embed(title="実行にはサーバーの管理権限が必要です。", color=discord.Color.red()))
            JST = datetime.timezone(datetime.timedelta(hours=9))
            invite = await self.bot.fetch_invite(招待url)
            embed = discord.Embed(title="招待リンクの情報", color=discord.Color.green()).add_field(name="サーバー名", value=f"{invite.guild.name}", inline=False).add_field(name="サーバーid", value=f"{invite.guild.id}", inline=False).add_field(name="招待リンク作成者", value=f"{invite.inviter.display_name if invite.inviter else "不明"} ({invite.inviter.id if invite.inviter else "不明"})", inline=False).add_field(name="招待リンクの使用回数", value=f"{invite.uses if invite.uses else "0"} / {invite.max_uses if invite.max_uses else "無限"}", inline=False)
            embed.add_field(name="チャンネル", value=f"{invite.channel.name if invite.channel else "不明"} ({invite.channel.id if invite.channel else "不明"})", inline=False)
            embed.add_field(name="メンバー数", value=f"{invite.approximate_member_count if invite.approximate_member_count else "不明"}", inline=False)
            embed.add_field(name="オンライン数", value=f"{invite.approximate_presence_count if invite.approximate_presence_count else "不明"}", inline=False)
            embed.add_field(name="作成時刻", value=f"{invite.created_at.astimezone(JST) if invite.created_at else "不明"}", inline=False)
            if invite.guild.icon:
                embed.set_thumbnail(url=invite.guild.icon.url)
            await ctx.reply(embed=embed)
            return
        if not ctx.guild.vanity_url:
            inv = await ctx.channel.create_invite()
            inv = inv.url
        else:
            inv = ctx.guild.vanity_url
        await ctx.reply(f"サーバー名: {ctx.guild.name}\nサーバーの人数: {ctx.guild.member_count}\n招待リンク: {inv}")

    @afk_set.command(name="short", description="短縮urlを作成します。(実行した人しか見えません)")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.choices(ドメイン=[
        app_commands.Choice(name='tinyurl.com',value="tiny"),
        app_commands.Choice(name='urlc.net',value="urlc"),
        app_commands.Choice(name='oooooo.ooo',value="ooo")
    ])
    async def short_url(self, ctx: commands.Context, ドメイン: app_commands.Choice[str], url: str):
        await ctx.defer(ephemeral=True)
        if ドメイン.value == "tiny":
            loop = asyncio.get_running_loop()
            s = await loop.run_in_executor(None, partial(pyshorteners.Shortener))
            url_ = await loop.run_in_executor(None, partial(s.tinyurl.short, url))
        elif ドメイン.value == "urlc":
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://urlc.net/', params={'url': url,'keyword': ''}) as response:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    url_ = soup.find({"button": {"class": "short-url-button noselect"}})["data-clipboard-text"]
        elif ドメイン.value == "ooo":
            class OOO:
                enc = ["o", "ο", "о", "ᴏ"]
                curr_ver = "oooo"

                def encode_url(self, url: str) -> str:
                    utf8_bytes = url.encode("utf-8")
                    base4_digits = ''.join(format(byte, '04b').zfill(8) for byte in utf8_bytes)
                    
                    b4str = ''
                    for i in range(0, len(base4_digits), 2):
                        b4str += str(int(base4_digits[i:i+2], 2))

                    oooified = ''.join(self.enc[int(d)] for d in b4str)
                    return self.curr_ver + oooified
            url_ = "https://ooooooooooooooooooooooo.ooo/" + OOO().encode_url(url)
        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> 短縮されたurl", description=f"{url_}", color=discord.Color.green()), ephemeral=True)

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_room(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "room_leave+" == custom_id:
                    await interaction.response.defer(ephemeral=True)
                    uid = interaction.message.embeds[0].footer.text.replace("uid:", "")
                    if uid == str(interaction.user.id):
                        await interaction.message.edit(embed=discord.Embed(title="退出しました。", color=discord.Color.red()), view=None)
                    else:
                        return await interaction.followup.send(ephemeral=True, content="あなたはボタンのオーナーではありません。")
                elif "coffee+" == custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        embed = interaction.message.embeds[0]
                        footer_text = embed.footer.text if embed.footer else ""
                        uid = footer_text.replace("uid:", "").strip()
                        if uid != str(interaction.user.id):
                            return await interaction.followup.send(ephemeral=True, content="あなたはボタンのオーナーではありません。")
                        current_count = 0
                        if embed.fields:
                            try:
                                current_count = int(embed.fields[0].value.replace("個", ""))
                            except ValueError:
                                return await interaction.followup.send(content="コーヒーの数が正しく取得できませんでした。", ephemeral=True)
                        new_count = current_count + 1
                        new_embed = discord.Embed(
                            title="作業部屋に入出しました。",
                            description=embed.description,
                            color=discord.Color.green()
                        )
                        new_embed.add_field(name="コーヒーの数", value=f"{new_count}個")
                        if embed.footer:
                            new_embed.set_footer(text=embed.footer.text)
                        await interaction.message.edit(embed=new_embed)

                    except Exception as e:
                        await interaction.followup.send(content=f"エラーが発生しました: {e}", ephemeral=True)
                elif "showembedowner" == custom_id:
                    await interaction.response.defer(ephemeral=True)
                    await interaction.followup.send(ephemeral=True, embed=discord.Embed(title="埋め込みの作成者", description=f"名前: {interaction.message.embeds[0].author.name}", color=discord.Color.green()).set_thumbnail(url=interaction.message.embeds[0].author.icon_url))
        except Exception as e:
            return

    @afk_set.command(name="room", description="作業部屋に入出します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def room(self, ctx: commands.Context, 作業内容: str):
        await ctx.defer()
        database = self.bot.async_db["Main"].StudyRoom
        await database.replace_one(
            {"User": ctx.author.id}, 
            {"User": ctx.author.id, "Room": 作業内容}, 
            upsert=True
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="退出する", style=discord.ButtonStyle.red, custom_id="room_leave+"))
        view.add_item(discord.ui.Button(label="コーヒーをオーダー", style=discord.ButtonStyle.blurple, custom_id="coffee+"))
        await ctx.reply(embed=discord.Embed(title="作業部屋に入出しました。", description=f"{作業内容}", color=discord.Color.green()).set_footer(text=f"uid:{ctx.author.id}"), view=view)

    @afk_set.command(name="wicklog-searcher", description="Wickのログをリスト化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def wicklog_searcher(self, ctx: commands.Context):
        await ctx.defer()
        log = discord.utils.get(ctx.guild.channels, name='wick-logs')
        if not log:
            return await ctx.reply("Wickのログチャンネルが見つかりません。")

        tl = ""
        async for lg in log.history(limit=30):
            if lg.author.display_name == "Wick":
                if not lg.embeds:
                    continue

                embed = lg.embeds[0]
                title = embed.title if embed.title else ""
                if "has been" in title:
                    parts = title.split("has been")
                    if len(parts) >= 2:
                        tl += f"{parts[0].strip()} has been{parts[1].strip()} {lg.jump_url}\n"

        if not tl:
            tl = "Wickによる該当ログが見つかりませんでした。"

        await ctx.reply(embed=discord.Embed(title="<:Success:1362271281302601749> Wickログ", description=f"{tl}", color=discord.Color.green()))

    @afk_set.command(name = "document", with_app_command = True, description = "ドキュメントを検索します。")
    @app_commands.choices(ドキュメント=[
        app_commands.Choice(name='discord.py',value="discord_py"),
    ])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def document(self, ctx, ドキュメント: app_commands.Choice[str], 検索ワード: str):
        await ctx.defer()
        if ドキュメント.name == "discord.py":
            async with aiofiles.open("Document/discord-py.html", mode='r', encoding="utf-8") as f:
                content = await f.read()
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find_all('a', {'class', "headerlink"})
            ti = []
            for t in title:
                if re.search(f"{検索ワード}", t["href"]):
                    ti.append(f"[{t["href"]}](https://discordpy.readthedocs.io/ja/latest/api.html{t["href"]})")
            ttt = ti[:10]
            if len(ttt) == 0:
                await ctx.reply(embed=discord.Embed(title=f"Discord.py - {検索ワード}", description=f"存在しませんでした。", color=discord.Color.red()).set_footer(text="Discord.py", icon_url="https://storage.googleapis.com/zenn-user-upload/topics/57b4918f2c.png"))
                return
            await ctx.reply(embed=discord.Embed(title=f"Discord.py - {検索ワード}", description=f"{"\n".join(ttt)}", color=discord.Color.blue()).set_footer(text="Discord.py", icon_url="https://storage.googleapis.com/zenn-user-upload/topics/57b4918f2c.png"))

    @afk_set.command(name="calculator", description="計算機を使用します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def calculator(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.reply(view=Calculator(), content="0")

    @afk_set.command(name="qrcode", description="QRコードを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def qrcode(self, ctx: commands.Context, テキスト: str):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="QRコード", color=discord.Color.green()).set_footer(text="QR code API", icon_url="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=QRCODEAPI").set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(テキスト)}"))

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_todo(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "todo_add":
                    if interaction.message.embeds[0].footer.text != str(interaction.user.id):
                        return await interaction.response.send_message(ephemeral=True, content="これはあなたのボタンではありません。")
                    class TodoAddModal(discord.ui.Modal, title="Todoの追加"):
                        naiyou = discord.ui.TextInput(
                            label='予定を入力',
                            required=True,
                            style=discord.TextStyle.short,
                            placeholder="洗濯"
                        )

                        async def on_submit(self, interaction_modal: discord.Interaction):
                            try:
                                await interaction_modal.response.defer(ephemeral=True)

                                count = 0
                                if interaction.message.embeds[0].description != "まだありません":
                                    count = int(re.search(r"\((\d+)\)", interaction.message.embeds[0].description.split("\n")[-1]).group(0).replace("(", "").replace(")", "")) + 1

                                # 新しいViewの作成
                                view = discord.ui.View()

                                # 元のメッセージのコンポーネントを解析
                                for action_row in interaction.message.components:
                                    for component in action_row.children:
                                        if component.type == discord.ComponentType.select:
                                            options = [
                                                discord.SelectOption(label=opt.label, value=opt.value, description=opt.description, emoji=opt.emoji, default=opt.default)
                                                for opt in component.options
                                                if opt.value != "madaarimasen"
                                            ]
                                            options.append(discord.SelectOption(label=f"{self.naiyou}", value=f"todo_select+{count}"))
                                            if options:
                                                select = discord.ui.Select(
                                                    placeholder=component.placeholder,
                                                    options=options,
                                                    custom_id=component.custom_id,
                                                    disabled=component.disabled,
                                                    min_values=component.min_values,
                                                    max_values=component.max_values
                                                )
                                                view.add_item(select)

                                        elif component.type == discord.ComponentType.button:
                                            button = discord.ui.Button(
                                                label=component.label,
                                                style=discord.ButtonStyle.success,
                                                custom_id=component.custom_id,
                                                emoji=component.emoji,
                                                url=component.url,
                                                disabled=component.disabled
                                            )
                                            view.add_item(button)

                                embed = interaction.message.embeds[0]
                                new_todo = f"❌{self.naiyou.value}"
                                if embed.description == "まだありません":
                                    new_description = new_todo + f" ({count})"
                                else:
                                    new_description = f"{embed.description}\n{new_todo} ({count})"

                                new_embed = discord.Embed(
                                    title=embed.title,
                                    description=new_description,
                                    color=discord.Color.from_str("#FFFFFF")
                                ).set_footer(text=f"{interaction.user.id}")

                                # メッセージを編集して予定を更新
                                await interaction.message.edit(embed=new_embed, view=view)

                            except Exception as e:
                                await interaction.followup.send(ephemeral=True, content=f"エラーが発生しました: `{e}`")

                    await interaction.response.send_modal(TodoAddModal())
                elif custom_id.startswith("todoend+"):
                    await interaction.response.defer(ephemeral=True)
                    try:
                        msg = await interaction.channel.fetch_message(int(custom_id.split("+")[2]))
                        for des in msg.embeds[0].description.split("\n"):
                            if re.search(r"\((\d+)\)", des).group(0).replace("(", "").replace(")", "") == custom_id.split("+")[1]:
                                embed = msg.embeds[0]
                                new_description = embed.description.replace(des, des.replace("❌", "✅"))
                                new_embed = discord.Embed(
                                    title=embed.title,
                                    description=new_description,
                                    color=discord.Color.from_str("#FFFFFF")
                                ).set_footer(text=f"{interaction.user.id}")
                                await msg.edit(embed=new_embed)
                                await interaction.followup.send(ephemeral=True, embed=discord.Embed(title="終了させました。", color=discord.Color.green()))
                                return
                    except Exception as e:
                        return
                elif custom_id.startswith("tododelete+"):
                    await interaction.response.defer(ephemeral=True)
                    try:
                        msg = await interaction.channel.fetch_message(int(custom_id.split("+")[2]))
                        for des in msg.embeds[0].description.split("\n"):
                            if re.search(r"\((\d+)\)", des).group(0).replace("(", "").replace(")", "") == custom_id.split("+")[1]:
                                embed = msg.embeds[0]
                                new_description = embed.description.replace(des + "\n", "").replace(des, "").replace(des + "\n", "").replace("\n" + des, "")
                                if new_description == "":
                                    new_description = "まだありません"
                                new_embed = discord.Embed(
                                    title=embed.title,
                                    description=new_description,
                                    color=discord.Color.from_str("#FFFFFF")
                                ).set_footer(text=f"{interaction.user.id}")

                                view = discord.ui.View()
                                for action_row in msg.components:
                                    for component in action_row.children:
                                        if component.type == discord.ComponentType.select:
                                            options = [
                                                discord.SelectOption(label=opt.label, value=opt.value, description=opt.description, emoji=opt.emoji, default=opt.default)
                                                for opt in component.options
                                                if opt.value != "madaarimasen"
                                            ]
                                            options.pop(int(custom_id.split("+")[1]))
                                            if options:
                                                select = discord.ui.Select(
                                                    placeholder=component.placeholder,
                                                    options=options,
                                                    custom_id=component.custom_id,
                                                    disabled=component.disabled,
                                                    min_values=component.min_values,
                                                    max_values=component.max_values
                                                )
                                                view.add_item(select)
                                            else:
                                                options.append(discord.SelectOption(label="まだありません", value="madaarimasen"))
                                                select = discord.ui.Select(
                                                    placeholder=component.placeholder,
                                                    options=options,
                                                    custom_id=component.custom_id,
                                                    disabled=component.disabled,
                                                    min_values=component.min_values,
                                                    max_values=component.max_values
                                                )
                                                view.add_item(select)

                                        elif component.type == discord.ComponentType.button:
                                            button = discord.ui.Button(
                                                label=component.label,
                                                style=discord.ButtonStyle.success,
                                                custom_id=component.custom_id,
                                                emoji=component.emoji,
                                                url=component.url,
                                                disabled=component.disabled
                                            )
                                            view.add_item(button)
                                await msg.edit(embed=new_embed, view=view)
                                await interaction.followup.send(ephemeral=True, embed=discord.Embed(title="削除しました", color=discord.Color.green()))
                                return
                    except Exception as e:
                        return
        except:
            return

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_select_todo(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 3:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "todo_select":
                    if interaction.message.embeds[0].footer.text != str(interaction.user.id):
                        return await interaction.response.send_message(ephemeral=True, content="これはあなたのボタンではありません。")
                    await interaction.response.defer(ephemeral=True)
                    for r in interaction.data["values"]:
                        if r == "madaarimasen":
                            return await interaction.followup.send(ephemeral=True, content="それは選択できません。")
                        else:
                            view = discord.ui.View()
                            view.add_item(discord.ui.Button(label="終了", style=discord.ButtonStyle.blurple, custom_id=f"todoend+{r.replace("todo_select+", "")}+{interaction.message.id}"))
                            view.add_item(discord.ui.Button(label="削除 (ベータ版)", style=discord.ButtonStyle.red, custom_id=f"tododelete+{r.replace("todo_select+", "")}+{interaction.message.id}"))
                            await interaction.followup.send(ephemeral=True, view=view, embed=discord.Embed(title="どうしますか？", color=discord.Color.green()))
                            return
        except:
            return

    @afk_set.command(name="todo", description="todoを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def todo(self, ctx: commands.Context, タイトル: str):
        view = discord.ui.View()
        view.add_item(discord.ui.Select(custom_id="todo_select", placeholder="予定を選択", options=[discord.SelectOption(label="まだありません", value="madaarimasen")]))
        view.add_item(discord.ui.Button(label="追加", style=discord.ButtonStyle.green, custom_id="todo_add"))
        await ctx.reply(embed=discord.Embed(title=タイトル, description="まだありません", color=discord.Color.from_str("#FFFFFF")).set_footer(text=f"{ctx.author.id}"), view=view)

    @afk_set.command(name="timer", description="タイマーをセットします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def timer(self, ctx: commands.Context, 秒数: int):
        if 秒数 > 300:
            return await ctx.reply(embed=discord.Embed(title="5分以上は計れません。", color=discord.Color.red()), ephemeral=True)
        db = self.bot.async_db["Main"].AlertQueue
        try:
            dbfind = await db.find_one({"ID": f"timer_{ctx.author.id}"}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="タイマーはすでにセットされています。", color=discord.Color.red()), ephemeral=True)
        if not dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="タイマーはすでにセットされています。", color=discord.Color.red()), ephemeral=True)
        await self.bot.alert_add(f"timer_{ctx.author.id}", ctx.channel.id, f"{ctx.author.mention}", f"{秒数}秒が経ちました。", "タイマーがストップされました。", 秒数)
        return await ctx.reply(embed=discord.Embed(title="タイマーをセットしました。", description=f"{秒数}秒です。", color=discord.Color.green()))

    @afk_set.command(name="fileuploader", description="ファイルをアップロードします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def fileuploader(self, ctx: commands.Context, ファイル: discord.Attachment):
        if ctx.author.id != 1335428061541437531:
            return await ctx.reply(embed=discord.Embed(title="現在メンテナンス中です。", description="復活時期は未定です。", color=discord.Color.red()), ephemeral=True)
        await ctx.defer(ephemeral=True)
        if ファイル.size > 3 * 1024 * 1024:
            return await ctx.reply("ファイルサイズが3MBを超えています。", ephemeral=True)
        try:
            orig_name = secure_filename(ファイル.filename)
            _, ext = os.path.splitext(orig_name)
            if not ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                return await ctx.reply(embed=discord.Embed(title="許可されていないファイルの種類です。", color=discord.Color.red(), description=".png .jpg .jpeg .gif .webp\nのみがアップロードできます。"), ephemeral=True)
            
            user_folder = f"./dashboard/static/files/{ctx.author.id}/"
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, partial(os.makedirs, user_folder, exist_ok=True))

            new_filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(f"./dashboard/static/files/{ctx.author.id}/", new_filename)
            await ファイル.save(file_path)
            await ctx.reply(embed=discord.Embed(title="アップロードしました。", color=discord.Color.green(), description=f"https://www.sharkbot.xyz/static/files/{ctx.author.id}/{new_filename}")
                            .set_footer(text="ファイルは流出しても責任取れません。よろしくお願いします。"))
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title="ファイルアップロード時にエラーが発生しました。", color=discord.Color.red()))

    @commands.command(name="hello", description="今日が始まってから何時間立ったかを計測します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def hello_time(self, ctx: commands.Context):
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        diff = now - midnight
        
        await ctx.reply(f'今日が始まってからの誤差は {diff} です。')

    @commands.command(name="custom_invite", description="カスタム招待リンクを作成します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def custom_invite(self, ctx: commands.Context, code: str):
        db = self.bot.async_db["Main"].CustomInvite
        try:
            dbfind = await db.find_one({"Code": code.replace(" ", "-")}, {"_id": False})
        except:
            return await ctx.reply("すでにそのコードは使用されています。")
        if not dbfind is None:
            return await ctx.reply("すでにそのコードは使用されています。")
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Code": code.replace(" ", "-")}, 
            {"Code": code.replace(" ", "-"), "URL": inv.url}, 
            upsert=True
        )
        await ctx.reply(f"カスタム招待リンクを作成しました。\nhttps://www.sharkbot.xyz/invite/{code.replace(" ", "-")}")

    @commands.command(name="category_ch_count", description="カテゴリの量をカウントします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def category_ch_count(self, ctx: commands.Context, カテゴリ: discord.CategoryChannel):
        await ctx.reply(f"{カテゴリ.name}のチャンネル数: {len(カテゴリ.channels)}個")

async def setup(bot):
    await bot.add_cog(ToolCog(bot))