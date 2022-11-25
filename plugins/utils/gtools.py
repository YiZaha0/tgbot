import os
import json
import asyncio
import random
import ffmpeg
import aiohttp

from urllib.parse import urljoin
from bs4 import BeautifulSoup 
from plugins import agents, run_cmd, req_content

class Entry:
	def __init__(self, name=None, title=None, link=None, summary=None):
		self.name = name 
		self.title = title 
		self.link = link 
		self.summary = summary 
	
	def __repr__(self):
		return json.dumps(self.__dict__, indent=4)
	
	async def extract_direct_urls(self):
		link = self.link
		cookies = {"auth": "aplnqLxgJbgtaoyFayGHsnA8ndd8z0BnmuGGwYwDl8BgPk3udnmsQsbW%2B4jXcmkfayLPOTXcZHip799T%2FTkUyg%3D%3D", "gogoanime": "hg9f7phuvd6ccm79k51unu6c62"}
		content = await req_content(link, cookies=cookies, headers={"User-Agent": random.choice(agents)})
		soup = BeautifulSoup(content, "html.parser")
		
		url_container = soup.find("div", "cf-download") 
		url_container = url_container.find_all("a") if url_container is not None else []
		
		urls = dict()
		for item in url_container:
			url = item["href"]
			quality = item.text.strip().split("x")[1]
			urls[quality] = url 
		
		return {"urls": urls, "Referer": "https://gogoplay1.com/"}
	
	async def extract_download_urls(self):
		link = self.link 
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

	async def extract_xstream_urls(self):
		download_urls = await self.extract_download_urls()
		xstream_url = download_urls["Xstreamcdn"]
		url_id = xstream_url.split("/")[-1]
		xtream_url = f"https://fembed9hd.com/f/{url_id}"
		code = f'''curl -A "uwu" -s -X POST "https://fembed9hd.com/api/source/{url_id}" -H "x-requested-with:XMLHttpRequest"'''
		result = (await run_cmd(code))[0]
		result = json.loads(result)["data"]
		
		urls = dict()
		for i in result:
			quality = i["label"]
			url = i["file"]
			urls[quality] = url
		
		return {"urls": urls, "Referer": xstream_url}
		
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
        raise
    return out_filename

def get_video_duration(path: str):
    probe = ffmpeg.probe(path)
    return int(float(probe['streams'][0]['duration']))
	
	
