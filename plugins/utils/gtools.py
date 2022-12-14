import os
import json
import asyncio
import random
import traceback
import ffmpeg
import aiohttp

from urllib.parse import urljoin
from bs4 import BeautifulSoup 
from AnilistPython import Anilist
from plugins import agents, run_cmd, req_content

class Entry:
	def __init__(self, name=None, title=None, link=None, summary=None):
		self.name = name 
		self.title = title 
		self.link = link 
		self.summary = summary 
	
	def __repr__(self):
		return json.dumps(self.__dict__, indent=4)
	
	async def get_download_urls(self):
		required_qualities = {"480p", "720p", "1080p"}
		ep_id = self.link.split("/")[-1]
		result = await req_content(
			f"https://api.consumet.org/anime/gogoanime/watch/{ep_id}",
			headers={"User-Agent": random.choice(agents)},
		)
		sources = result.get("sources")
		if not sources: return
		qualities = {i["quality"] for i in sources}

		if required_qualities.issubset(qualities):
			data = dict()
			result["headers"]["User-Agent"] = random.choice(agents)
			for item in sources:
				data[item["quality"]] = item["url"] 
			
			return {
				"data": data,
				"headers": result["headers"] 
			}
	
async def extract_download_urls(link:str) -> dict:
	cookies = {"auth": "aplnqLxgJbgtaoyFayGHsnA8ndd8z0BnmuGGwYwDl8BgPk3udnmsQsbW%2B4jXcmkfayLPOTXcZHip799T%2FTkUyg%3D%3D", "gogoanime": "hg9f7phuvd6ccm79k51unu6c62"}
	content = await req_content(link, cookies=cookies, headers={"User-Agent": random.choice(agents)})
	soup = BeautifulSoup(content, "html.parser")
		
	url_container = soup.find("div", "cf-download") 
	url_container = url_container.find_all("a") if url_container is not None else []
		
	urls = dict()
	for item in url_container:
		url = item["href"]
		quality = item.text.strip().split("x")[1] + "p"
		urls[quality] = url 
		
	return {
		"urls": urls, 
		"headers": {"Referer": "https://gogoplay1.com/"}
	}
	
async def extract_source_urls(link: str) -> dict:
	content = await req_content(link, headers={"User-Agent": random.choice(agents)})
	soup = BeautifulSoup(content, "html.parser")
		
	multi_container = soup.find("div", "anime_muti_link")
	multi_container = multi_container.find_all("li") if multi_container is not None else []
		
	urls = dict()
	for item in multi_container:
		site = item.text.replace(item.span.text, "").strip()
		link = item.a["data-video"]
		urls[site] = link 
		 
	return urls

async def extract_xstream_urls(link: str) -> dict:
	download_urls = await extract_source_urls(link)
	xstream_url = download_urls["Xstreamcdn"]
	url_id = xstream_url.split("/")[-1]
	xtream_url = f"https://fembed9hd.com/f/{url_id}"
	code = f'''curl -A "uwu" -s -X POST "https://fembed9hd.com/api/source/{url_id}" -H "x-requested-with:XMLHttpRequest"'''
	result = (await run_cmd(code))[0]
	result = json.loads(result)["data"]
	if not isinstance(result, dict): return
	urls = dict()
	for i in result:
		quality = i["label"]
		url = i["file"]
		urls[quality] = url
		
	return {
		"urls": urls,
		"headers": {"Referer": xstream_url}
	}
		
async def GogoFeed():
	base = "https://gogoanime.dk/"
	content = await req_content(base, headers={"User-Agent": random.choice(agents)})
	soup = BeautifulSoup(content, "html.parser")
	
	container = soup.find("div", "last_episodes loaddub")
	name_items = container.find_all("p", "name")
	episode_items = container.find_all("p", "episode")
	
	entries = []
	for name, ep in zip(name_items, episode_items):
		anime_name = name.text
		ep_title = f"{name.text} - {ep.text}"
		ep_link = urljoin(base, name.a["href"])
		ep_summary = f"{ep.text} of {name.text} is out!"
		ep_entry = Entry(anime_name, ep_title, ep_link, ep_summary)
		entries.append(ep_entry)
	
	return entries

def gen_video_ss(file):
    probe = ffmpeg.probe(file)
    time = random.randint(0, int(float(probe['streams'][0]['duration'])))
    width = probe['streams'][0]['width']
    out_filename = os.path.splitext(file)[0] + f"_{time}.jpg"
    try:
        (
            ffmpeg
            .input(file, ss=time)
            .filter('scale', width, -1)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except:
        traceback.print_exc()
    return out_filename

def get_video_duration(path: str):
    probe = ffmpeg.probe(path)
    return int(float(probe['streams'][0]['duration']))

def get_anime_name(name: str) -> str:
    Api = Anilist()
    try:
        anime = Api.get_anime(name)
    except:
        anime = dict()
    return anime.get("name_english", None)

def get_anime_cover(name: str) -> str:
    Api = Anilist()
    try:
        anime = Api.get_anime(name)
    except:
        anime = dict()
    return anime.get("cover_image", None)

