import os
import glob
import asyncio
import logging

from pathlib import Path 
from plugins import app, bot, load_plugin, scheduler, LOG_CHAT
from plugins.tools import update_thumbnail
from plugins.readp import manhwa_updater
from fastapi import FastAPI, Request

#For Koyeb
fast = FastAPI()
@app.get("/")
def root(request: Request):
	return {"status": "ok", "root": request.url.hostname}

#LOGGING
LOG_FILE = "LOGS.txt"
not os.path.exists(LOG_FILE) or os.remove(LOG_FILE)
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO, handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

#LOADING
path = "./plugins/*py"
files = glob.glob(path)
for name in files:
	plugin_path = Path(name)
	plugin_name = plugin_path.stem
	try:
		load_plugin(plugin_name.replace(".py", ""))
	except BaseException as e:
		logging.exception(e)

#LOOP
loop = asyncio.get_event_loop_policy().get_event_loop()

#LOAD_THUMB
loop.run_until_complete(update_thumbnail())

#STARTING
bot.send_message(LOG_CHAT, "**Bot is alive now❗**")
logging.info("»Successfully Deployed Bot!")
loop.create_task(manhwa_updater())
app.run()
