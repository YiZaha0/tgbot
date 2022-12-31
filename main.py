import os
import glob
import asyncio
import uvloop
import logging

#uvloop.install()
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


from pathlib import Path 
from plugins import *
from plugins.tools import update_thumbnail
from plugins.readp import manhwa_updater
		
#LOGGING
LOG_FILE = "Useless.log"
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

#CREATING TASKS
loop.create_task(manhwa_updater())

#CREATING CACHE DIRECTORY
os.makedirs("cache", exist_ok=True)

#STARTING
scheduler.start() #AsyncIOScheduler
bot.start(bot_token=Config.BOT_TOKEN)
logger.info("»Telethon Client started successfully.")
if uB:
	uB.start()
	logger.info("»Pyrogram User Client started successfully.")
app.start()
logger.info("»Pyrogram Bot Client started successfully.")
app.send_message(LOG_CHAT, "<b>Bot is Online!</b>")
logger.info("»Deployed Successfully!")
bot.run_until_disconnected()


