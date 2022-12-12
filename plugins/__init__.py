#IMPORTS
import importlib, inspect, re, asyncio, time, sys, os, requests, shutil, aiohttp, aiofiles, logging
import pyromod.listen
from urllib.parse import unquote
from pathlib import Path
from telethon import events
from asyncio import sleep
from config import Config
from .utils.fast_telethon import uploader, downloader
from html_telegraph_poster import TelegraphPoster
from pymongo import MongoClient
from telethon import TelegramClient
from pyrogram import Client 
from telethon import events 
from telethon.tl.custom import Message
from telethon.tl.types import MessageService
from telethon.errors import MessageDeleteForbiddenError, MessageNotModifiedError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

#CLIENTS
bot = TelegramClient("TestBot", Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
app = Client("TestBot-Pyro", Config.API_ID, Config.API_HASH, bot_token=Config.BOT_TOKEN)

#DB
mongo = MongoClient(Config.MONGO_URL)
mongodb = mongo["TESTDB"]
db = mongodb["MAIN"]

#VARS
bot_start_time = time.time()
logger = logging.getLogger("Bot")
sudo_users = Config.SUDOS or "5304356242 5370531116 5551387300"
sudo_users = sudo_users.split()
SUDOS = []
for sudo_id in sudo_users:
	try:
		sudo_id = int(sudo_id)
	except:
		pass 
	SUDOS.append(sudo_id)
LOG_CHAT = Config.LOG_CHAT or -1001568226560
agents = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5', 'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5', 'Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15']
scheduler = AsyncIOScheduler()

#FUNCs
def get_db(variable, cn="MAIN"):
	if mongodb[cn].find_one():
		for var in mongodb[cn].find({variable: {"$exists": 1}}):
			return var[variable]

def del_db(variable, cn="MAIN"):
	if mongodb[cn].find_one():
		for var in mongodb[cn].find({variable: {"$exists": 1}}):
			mongodb[cn].delete_one(var)

def add_db(var, value, cn="MAIN"):
	is_var = get_db(var)
	if is_var:
		del_db(var)
	mongodb[cn].insert_one({var: value})

def load_plugin(plugin_name):
    if plugin_name.startswith("__"):
    	pass
    else:
    	path = Path(f"plugins/{plugin_name}.py")
    	name = "plugins.{}".format(plugin_name)
    	spec = importlib.util.spec_from_file_location(name, path)
    	load = importlib.util.module_from_spec(spec)
    	load.logger = logging.getLogger(plugin_name)
    	spec.loader.exec_module(load)
    	sys.modules["plugins." + plugin_name] = load
    	logging.info("»Bot has imported " + plugin_name)

def restart_bot():
	os.system("git pull -f && pip3 install --quiet -U -r requirements.txt")
	os.execl(sys.executable, "python3", "main.py")
bot.restart = restart_bot

def check(inp):
    if len(str(inp)) == 1:
        inp = f"0{inp}"
        return inp
    return inp

def readable_time(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    print(type(minutes))
    return (
        (f"{int(days)} day(s), " if days else "")
        + (f"{check(hours)}:" if hours else "00:")
        + (f"{check(minutes)}:" if minutes else "00:")
        + str((check(seconds)) if seconds else "00")
    )

async def run_cmd(cmd, run_code=0):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    error = stderr.decode().strip() or None
    output = stdout.decode().strip()
    return output, error
   
async def eor(event, text=None, **args):
    time = args.get("time", None)
    edit_time = args.get("edit_time", None)
    if "edit_time" in args:
        del args["edit_time"]
    if "time" in args:
        del args["time"]
    if "link_preview" not in args:
        args["link_preview"] = False
    args["reply_to"] = event.reply_to_msg_id or event
    if event.out and not isinstance(event, MessageService):
        if edit_time:
            await sleep(edit_time)
        if "file" in args and args["file"] and not event.media:
            await event.delete()
            ok = await event.client.send_message(event.chat_id, text, **args)
        else:
            try:
                try:
                    del args["reply_to"]
                except KeyError:
                    pass
                ok = await event.edit(text, **args)
            except MessageNotModifiedError:
                ok = event
    else:
        ok = await event.client.send_message(event.chat_id, text, **args)

    if time:
        await sleep(time)
        return await ok.delete()
    return ok

async def eod(event, text=None, **kwargs):
    kwargs["time"] = kwargs.get("time", 8)
    return await eor(event, text, **kwargs)

def post_telegraph(title, content, author, author_url=None):
    post_client = TelegraphPoster(use_api=True)
    post_client.create_api_token(author)
    post_page = post_client.post(
        title=title,
        author=author,
        author_url=author_url,
        text=content)
    return post_page["url"]

async def req_content(url, method="GET", data=None, *args, **kwargs):
	async with aiohttp.ClientSession() as session:
		if method.lower() == "get":
			response = await session.get(url, *args, **kwargs)
		elif method.lower() == "post":
			response = await session.post(url, data=data or dict(), **kwargs)
		else:
			raise ValueError
		content = await response.read()
		return content

async def req_url(url, method="GET", data=None, *args, **kwargs):
	async with aiohttp.ClientSession() as session:
		if method.lower() == "get":
			response = await session.get(url, *args, **kwargs)
		elif method.lower() == "post":
			response = await session.post(url, data=data or dict(), **kwargs)
		else:
			raise ValueError
		return response

async def req_download(download_url, filename=None, progress_callback=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url, headers=headers, timeout=None) as response:
            if not filename:
                filename = unquote(download_url.rpartition("/")[-1])
            total_size = int(response.headers.get("content-length", 0)) or None
            downloaded_size = 0
            start_time = time.time()
            with open(filename, "wb") as f:
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                    if progress_callback and total_size:
                        await _maybe_await(
                            progress_callback(downloaded_size, total_size)
                        )
            return filename, time.time() - start_time
