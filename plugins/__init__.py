#IMPORTS
import importlib, inspect, re, asyncio, time, sys, os, requests, shutil, aiohttp, aiofiles, logging
import pyromod.listen
from urllib.parse import unquote
from pathlib import Path
from asyncio import sleep
from config import Config
from .utils.progress_cb import progress
from html_telegraph_poster import TelegraphPoster
from pymongo import MongoClient
from pyrogram import Client 
from apscheduler.schedulers.asyncio import AsyncIOScheduler


#VARS
bot_start_time = time.time()
logger = logging.getLogger("Useless [Bot]")
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
OWNER = Config.OWNER or 5370531116
agents = [
 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
 'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
 'Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15'
]
scheduler = AsyncIOScheduler()


#CLIENTS
app = Client(
	"TestBot-Pyro",
	api_id=Config.API_ID,
	api_hash=Config.API_HASH,
	bot_token=Config.BOT_TOKEN
)

uB = None
if Config.PYRO_SESSION and Config.UB:
	uB = Client(
		"TestUser",
		 api_id=Config.API_ID,
		api_hash=Config.API_HASH,
		session_string=Config.PYRO_SESSION
	)

#DB
mongo = MongoClient(Config.MONGO_URL)
mongodb = mongo["TESTDB"]
db = mongodb["MAIN"]


#FUNCs
def get_db(key, cn="MAIN"):
	if not mongodb[cn].find_one():
		return 
	for item in mongodb[cn].find():
		try:
			return item[key]
			break
		except:
			continue 

def del_db(variable, cn="MAIN"):
	if mongodb[cn].find_one():
		for var in mongodb[cn].find({variable: {"$exists": 1}}):
			mongodb[cn].delete_one(var)

def add_db(var, value, cn="MAIN"):
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
    	logger.info("»Bot has imported " + plugin_name)

def restart_bot():
	os.system("git pull -f && pip3 install --quiet -U -r requirements.txt")
	os.execl(sys.executable, "python3", "main.py")
app.reboot = restart_bot

def check(inp):
    if len(str(inp)) == 1:
        inp = f"0{inp}"
        return inp
    return inp

def readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

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

def post_telegraph(title, content, author, author_url=None):
    post_client = TelegraphPoster(use_api=True, telegraph_api_url='https://api.graph.org')
    post_client.create_api_token(author)
    post_page = post_client.post(
        title=title,
        author=author,
        author_url=author_url,
        text=content)
    return post_page["url"]

async def req_content(url, method="GET", data=None, *args, **kwargs):
	async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
		if method.lower() == "get":
			response = await session.get(url, *args, **kwargs)
		elif method.lower() == "post":
			response = await session.post(url, data=data or dict(), **kwargs)
		else:
			raise ValueError

		if response.content_type == "application/json":
			content = await response.json()
		else:
			content = await response.read()
	return content

async def req_url(url, method="GET", data=None, *args, **kwargs):
	session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) 
	if method.lower() == "get":
		response = await session.get(url, *args, **kwargs)
	elif method.lower() == "post":
		response = await session.post(url, data=data or dict(), **kwargs)
	else:
		raise ValueError 
	return response


async def req_download(download_url, filename=None, progress_callback=None, headers=None):
    await asyncio.sleep(0.1)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        async with session.get(download_url, headers=headers, timeout=90) as response:
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

async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value

chat_photos = dict()
async def get_chat_pic(chat_id: int, refresh: bool = None):
	if not refresh and chat_id in chat_photos:
		return chat_photos[chat_id]
		
	try:
		chat = await app.get_chat(chat_id)
		if hasattr(chat, "photo") and chat.photo:
			photo = await app.download_media(chat.photo.big_file_id)
			chat_photos[chat_id] = photo 
			return photo 
	except:
		pass

invitation_links = dict()
async def get_chat_invite_link(chat_id: int, refresh: bool = None):
	if not refresh and chat_id in invitation_links:
		return invitation_links[chat_id]
	try:
		chat = await app.get_chat(chat_id)
		link = f"https://t.me/{chat.username}" if chat.username else chat.invite_link
		invitation_links[chat_id] = link 
		return link 
	except:
		return None
