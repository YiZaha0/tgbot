import random 
import traceback

from AnilistPython import Anilist

from .utils.gtools import gen_video_ss, get_video_duration, get_anime_name, get_anime_cover
from .utils.ani import get_anime_manga
from . import *


FEED_CHAT = -1001633233596
border_stickers = [
    "CAACAgUAAxkBAAJlZWO5yjGyvnaYWK9Y-M3oNjelzR2ZAAIfAANDc8kSq8cUT3BtY9AeBA",
    "CAACAgUAAxkBAAJlY2O5yigf1GFcHBRe9lUKapoXzWd2AAI4AANDc8kSqEy-nx6sFQoeBA",
    "CAACAgUAAxkBAAJlYmO5yiP3hYRxyZ4hB0QJr3f-WQ2fAAI8AANDc8kS7jdGbja_UggeBA",
    "CAACAgUAAxkBAAJlYGO5yiK5RixNuzUHGxk0w-Ie5_FtAAI_AANDc8kSLDGyuwP6tQ8eBA",
    "CAACAgUAAxkBAAJlX2O5yiKlgHjADxVbC8SNxYu17cdEAAI-AANDc8kSMh37AsG_DNYeBA",
    "CAACAgUAAxkBAAJlXmO5yh3Ns-mJ_gqQUxLj8FnhGi2EAAI6AANDc8kSXkFqoI4WW6EeBA",
]

async def get_entries():
	page = await req_content(
		"https://animepahe.com/api?m=airing",
		headers={"User-Agent": random.choice(agents)},
	)

	new_entries = list()
	for entry in page["data"]:
		if entry["completed"]:
			continue 
		entry_id = entry["anime_title"] + " - " + str(entry["episode"])
		new_entries.append(entry)

	new_entries.reverse()
	
	return new_entries 

async def parse_dl(entry: dict):
	api = "https://api.consumet.org/anime/animepahe/watch/"
	ep_id = entry["session"]
	for _  in range(6):
		data = await req_content(
		f"{api}{ep_id}",
		headers={"User-Agent": random.choice(agents)}
		)
		if not isinstance(data, dict):
			await asyncio.sleep(2)
			continue 

		if data.get("sources") and len(data.get("sources")) > 2:
			return data
			break

async def upload_entry(entry: dict, data: dict = None, chat: int = FEED_CHAT, as_video: bool = False):
	dl_data = data or await parse_dl(entry)
	anime_name = entry["anime_title"]
	ep = entry["episode"]
	eng_name = get_anime_name(anime_name)
	
	try:
		anime = await get_anime_manga(anime_name, "anime_anime", author="Ongoing Anime Seasons", author_url="https://t.me/Ongoing_Anime_Seasons")
	except:
		anime = None 
		
	Process = list()
	Files = dict()
	for source in dl_data["sources"]:
		url = source["url"]
		quality = source["quality"]+"p"
		file = f"./cache/{eng_name or anime_name} - {ep} [{quality}] [@Ongoing_Anime_Seasons].mp4"
		Process.append(run_cmd(
			f'ffmpeg -y -headers "Referer: {dl_data["headers"]["Referer"]}" -i "{url}" -c copy -bsf:a aac_adtstoasc "{file}"'
			)
		)
		Files[quality] = file 
	
	await asyncio.gather(*Process)
	
	if anime and as_video is False:
		anime_caption, anime_img, _ = anime 
		anime_caption = anime_caption.replace(anime_caption.split("\n")[-2]+"\n", "").strip()
		anime_id = anime_img.split("/")[-1] 
		anime_img = f"./cache/anilist_img-{anime_id}.jpg" if os.path.exists(f"./cache/anilist_img-{anime_id}.jpg") else (await req_download(anime_img, filename=f"./cache/anilist_img-{anime_id}.jpg"))[0]
		anime_cover = get_anime_cover(anime_name)
		anime_cover_path = f"./cache/anilist_cover_img-{anime_id}.jpg" if anime_cover else None
		await app.send_photo(chat, anime_img, caption=anime_caption)
		
	for quality, file in Files.items():
		if not os.path.exists(file):
			logger.info(f"»Insufficient amount of files available for {anime_name} - {ep} (Probably due to some error in download), Quiting Upload.")
			break 
			return
		
		if anime and as_video is False:
			if not anime_cover_path:
				thumb = gen_video_ss(file)
			else:
				thumb = (await req_download(anime_cover, filename=anime_cover_path))[0]
			
			await app.send_document(
				chat,
				file,
				caption=f"<b>Episode {ep} • {quality}</b>",
				thumb=thumb,
			)

		else:
			thumb = gen_video_ss(file)
			duration = get_video_duration(file)
			caption = f"<b>{eng_name} | {anime_name}</b>\n\n" if eng_name else f"<b>{anime_name}</b>\n\n"
			caption += f"<b>♤ Episode:</b> <code>{ep}</b>\n"
			caption += f"<b>♤ Quality:</b> <code>{quality}</code>\n"
			caption += f"<b>♤ Duation:</b> <code>{readable_time(duration)}</code>"
			
			await app.send_video(
				chat, 
				file,
				caption=caption,
				duration=duration,
			)

		os.remove(file)
		os.remove(thumb)
	
	await app.send_cached_media(chat, random.choice(border_stickers))
	
async def update_feed():
	entries = await get_entries()
	last_entries = get_db("PaheFeed_Entries")
	if last_entries is None:
		add_db("PaheFeed_Entries", list())
		
	if not entries:
		logger.info("»PaheFeed: No Entries Found.")
		
	else:
		for entry in entries:
			entry_id = entry["anime_title"] + " - " + str(entry["episode"])
			
			if entry_id in last_entries:
				continue 
				
			logger.info(f"»PaheFeed: New Anime Released → {entry_id}.")
			parsed_dl = await parse_dl(entry)
			
			if parsed_dl:
				try:
					await upload_entry(entry, data=parsed_dl)
				except Exception as e:
					logger.info(f"»PaheFeed: Got Error While Uploading Entry {entry_id}: {e}.")
					traceback.print_exc()
				
				last_entries.append(entry_id)
				
			else:
				logger.info(f"»PaheFeed: Download Urls Not Found for Entry {entry_id}.")
	
	add_db("PaheFeed_Entries", last_entries)

async def autofeed():
	sleep_time = 180
	while True:
		try:
			logger.info("»PaheFeed: New Process Started!")
			await update_feed()
			logger.info("»PaheFeed: Process Completed!")
		except Exception as exc:
			logger.info(f"»Got Error While Updating PaheFeed: {exc}")
			traceback.print_exc()
		await asyncio.sleep(sleep_time)
