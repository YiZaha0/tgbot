from .utils.gtools import *
from . import *

ReCache = list()
GFEED = Config.GFEED or -1001633233596
border_stickers = [
    'CAACAgUAAx0CXXk9AANKxGNBnX8qYFetcrtuDshld0wS8jv2AAImBgACN83hViwucrfDIJViHgQ',
    'CAACAgUAAx0CXXk9AANKw2NBnUaNd8iGX57AlfWiXn6NBwSZAAKXBAACkS3gVn24I44fU76JHgQ', 
    'CAADBQADywUAAjIR4Va7IL3zu24i0gI',
    'CAADBQADMgUAAtmH4FZaVf8VJYihogI',
]

async def upload_entry(entry: Entry):
	result = await entry.get_download_urls()
	Process = list()
	Files = dict()
	for quality, url in result["data"].items():
		if not quality.endswith("0p"):
			continue 
		filename = f"./cache/{entry.title} [{quality}] [@Ongoing_Anime_Seasons].mp4"
		Process.append(
			run_cmd(
				f'ffmpeg -i "{url}" -c copy -bsf:a aac_adtstoasc "{filename}"'
			)
		)
		Files[quality] = filename
	try:
		await asyncio.gather(*Process)
	except Exception as e:
		logger.info(f"»GogoFeed: Got Error while downloading files of {entry.title}: {e.__class__.__name__}: {e}")
		return 
	
	for quality, file in Files.items():
		if not os.path.exists(file):
			continue
		try:
			duration = get_video_duration(file)
			thumb = gen_video_ss(file)
			caption = """<b>{} • {}</b>"""
			await app.send_video(
				GFEED,
				file,
				caption=caption.format(
					entry.title,
					quality,
				),
				duration=duration,
				thumb=thumb,
			)
			os.remove(file)
		except Exception as e:
			logger.info(f"»GogoFeed: Got Error while uploading files of {entry.title}: {e.__class__.__name__}: {e}") 
	await app.send_sticker(GFEED, random.choice(border_stickers))
	
async def auto_gfeed():
	feed = await GogoFeed()
	logger.info("»GogoFeed: Started!")
	last_entry = get_db("GFEED_last_entry")
	new_entries = []
	for entry in feed:
		if entry.title == last_entry:
			break 
		new_entries.append(entry)
		
	new_entries.reverse()

	if new_entries:
		logger.info("»GogoFeed: New Entries:\n" + "".join(f"→{e.title}\n" for e in new_entries))
	else:
		logger.info("»GogoFeed: No New Entries")

	for entry in new_entries:
		result = await entry.get_download_urls()
		if not result:
			logger.info(f"»GogoFeed: No urls found for {entry.title}, adding to CACHE.")
			ReCache.append(entry)
		else:
			await upload_entry(entry)
		add_db("GFEED_last_entry", entry.title)
	await auto_ReCache()
	logger.info("»GogoFeed: Ended!")
			
async def auto_ReCache():
	logger.info("»GogoFeed (ReCache): Started!")
	for entry in ReCache:
		result = await entry.get_download_urls()
		if result: 
			await upload_entry(entry) 
			ReCache_remove(entry)
	logger.info("»GogoFeed (ReCache): Ended!")

def ReCache_remove(entry):
	for e in ReCache:
		if entry == e:
			ReCache.remove(e)
			
scheduler.add_job(auto_gfeed, "interval", minutes=5, max_instances=1)
	
