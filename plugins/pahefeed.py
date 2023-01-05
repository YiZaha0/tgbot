import random 

from .utils.gtools import gen_video_ss, get_video_duration, get_anime_name
from . import *

ReCache = list()
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
		headers={"User-Agent": random.choice(agents)},
	)
	last_entry = get_db("Last_PaheFeed_Entry")
	new_entries = list()
	for entry in page["data"]:
		if entry["completed"]:
			continue 
		entry_id = entry["anime_title"] + " - " + str(entry["episode"])
		if entry_id == last_entry:
			break 
		new_entries.append(entry)
	new_entries.reverse()
	return new_entries 

def parse_dl(entry: dict) -> dict:
	api = "https://api.consumet.org/anime/animepahe/watch/"
	ep_id = entry["session"]
	try:
		data = requests.get(
		f"{api}{ep_id}",
		headers={"User-Agent": random.choice(agents)}
		).json()
	except:
		return
	if isinstance(data, dict) and data.get("sources") and len(data.get("sources")) > 2:
		return data
	
async def upload_entry(entry: dict):
	dl_data = parse_dl(entry)
	og_name = entry["anime_title"]
	eng_name = get_anime_name(name)
	if eng_name and eng_name.lower() != og_name.lower():
		name = f"{eng_name} | {og_name}"
	ep = entry["episode"]
	Process = list()
	Files = dict()
	for source in dl_data["sources"]:
		quality = source["quality"] + "p"
		filename = f"cache/{eng_name or og_name} [Ep - {ep}] [{quality}] [@Ongoing_Anime_Seasons].mp4"
		url = source["url"]
		Process.append(
			run_cmd(
				f'ffmpeg -y -headers "Referer: {dl_data["headers"]["Referer"]}" -i "{url}" -c copy -bsf:a aac_adtstoasc "{filename}"'
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
			caption = f"<b>{name}</b>\n\n<b>♤ Episode:</b> {check(ep)}\n<b>♤ Quality:</b> {quality}"
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
		logger.info("»PaheFeed: New Entries:" + "".join("\n→" + e["anime_title"] + " - " + str(e["episode"]) for e in entries))
		for entry in entries:
			entry_id = entry["anime_title"] + " - " + str(entry["episode"])
			parsed_dl = parse_dl(entry)
			if parsed_dl:
				try:
					await upload_entry(entry)
				except Exception as e:
					logger.info(f"»PaheFeed: Got Error While Uploading Entry {entry_id}: {e}")
			else:
				logger.info(f"»PaheFeed: Download Urls Not Found for Entry {entry_id}, Adding it to ReCache.")
				ReCache.append(entry)
			add_db("Last_PaheFeed_Entry", entry_id)
	
	logger.info("»PaheFeed (ReCache): Started!")
	await auto_ReCache()
	logger.info("»PaheFee (ReCache): Ended!")
	
	logger.info("»PaheFeed: Ended!")

async def auto_ReCache():
	for entry in ReCache:
		entry_id = entry["anime_title"] + " - " + str(entry["episode"])
		parsed_dl = parse_dl(entry)
		if parsed_dl:
			try:
				await upload_entry(entry)
			except Exception as e:
				logger.info(f"»PaheFeed (ReCache): Got Error While Uploading Entry {entry_id}: {e}")
			ReCache_remove(entry)
			
def ReCache_remove(entry):
	for e in ReCache:
		if e == entry:
			ReCache.remove(e)
			
scheduler.add_job(autofeed, "interval", minutes=1, max_instances=1)
		
