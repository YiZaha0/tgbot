import random 

from .utils.gtools import gen_video_ss, get_video_duration, get_anime_name
from . import *

FEED_CHAT = -1001633233596
border_stickers = [
    'CAACAgUAAx0CXXk9AANKxGNBnX8qYFetcrtuDshld0wS8jv2AAImBgACN83hViwucrfDIJViHgQ',
    'CAACAgUAAx0CXXk9AANKw2NBnUaNd8iGX57AlfWiXn6NBwSZAAKXBAACkS3gVn24I44fU76JHgQ', 
    'CAADBQADywUAAjIR4Va7IL3zu24i0gI',
    'CAADBQADMgUAAtmH4FZaVf8VJYihogI',
]

async def get_entries():
	page = await req_content(
		"https://animepahe.com/api?m=airing",
		headers={"User-Agent": random.choice(agents)}
	)
	last_entry = get_db("Last_PaheFeed_Entry")
	new_entries = list()
	for entry in page["data"]:
		if entry["completed"]:
			continue 
		entry_id = entry["anime_name"] + " - " + entry["episode"]
		if entry_id == last_entry:
			break 
		new_entries.append(entry)
	new_entries.reverse()
	return new_entries 

async def upload_entry(entry: dict):
	api = "https://api.consumet.org/anime/animepahe/watch/"
	ep_id = entry["session"]
	dl_data = await req_content(
		f"{api}{epi_id}"
	)
	
	name = entry["anime_name"]
	eng_name = get_anime_name(name)
	if eng_name and eng_name.lower() != name.lower():
		name = f"{eng_name} | {name}"
	ep = entry["episode"]
	Process = list()
	Files = dict()
	for source in dl_data["sources"]:
		quality = source["quality"] + "p"
		filename = f"cache/{name} [Ep - {ep}] [{quality}] [@Ongoing_Anime_Seasons].mp4"
		url = source["url"]
		Process.append(
			run_cmd(
				f'ffmpeg -headers "Referer: {dl_data["headers"]["Referer"]}" -i "{url}" "{filename}"'
			)
		)
		Files[quality] = filename 
		
	await asyncio.gather(*Process)
		
	for quality, file in Files.items():
		if not os.path.exists(file):
			continue 
		try:
			thumb = gen_video_ss(file)
			duration = get_video_duration(file)
			caption = f"<b>{name}</b>\n\n<b>♤ Episode:</b> <i>{ep}</i>\n<b>♤ Quality:</b> <i>{quality}</i>"
			await app.send_video(
				FEED_CHAT,
				file,
				caption=caption,
				thumb=thumb,
				duration=duration,
			)
			os.remove(thumb)
			os.remove(file)
		except Exception as e:
			logger.info(
				f"»PaheFeed: Got Error while uploading files of {entry.title}: {e.__class__.__name__}: {e}",
			)
	await app.send_sticker(
		FEED_CHAT, 
		random.choice(
			border_stickers
		),
	)
			
async def autofeed():
	logger.info("»PaheFeed: Started!")
	entries = await get_entries()
	if not entries:
		logger.info("»PaheFeed: No Entries Found")
	else:
		logger.info("»PaheFeed: New Entries:" + "".join(e["anime_name"] + " - " + e["episode"] for e in entries))
		for entry in entries:
			entry_id = entry["anime_name"] + " - " + entry["episode"]
			try:
				await upload_entry(entry)
			except:
				logger.info("»PaheFeed: Got Error while upload entry: {entry_id}")
			add_db("Last_PaheFeed_Entry", entry_id)
	logger.info("»PaheFeed: Ended!")

scheduler.add_job(autofeed, "interval", minutes=1, max_instances=1)
		
