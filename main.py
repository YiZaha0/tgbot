import os
import glob
import logging

from pathlib import Path 
from plugins import app, bot, load_plugin, scheduler, LOG_CHAT
from plugins.tools import update_thumbnail

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

#LOAD_THUMB
bot.loop.run_until_complete(update_thumbnail())

#STARTING
if __name__ == "__main__":
	print("»Successfully Deployed Bot!")
	bot.send_message(LOG_CHAT, "**Bot is alive now❗**")
	scheduler.star()
	app.run()
