import requests
import asyncio
import cloudscraper

from search_engine_parser import GoogleSearch
from pyrogram import filters, types
from telethon import functions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .utils.auws import *
from . import *


def get_link(link, cloud=False):
	session = requests.Session()
	if cloud:
		session = cloudscraper.create_scraper()
	r = session.get(link)
	r.raise_for_status()
	return r.url

gsearch_results = dict() 
async def gsearch(name, site="-20"):
	if not site.startswith("-"):
		query = f"{name} site:{site}"
	elif site == "-20":
		query = f"{name} site:Hentai20.com"
	elif site == "-3z":
		query = f"{name} site:Hentai3z.com"
	if gsearch_results.get(query):
		return gsearch_results[query]
	google = GoogleSearch()
	result = await google.async_search(f"{name} site:{site}")
	links = result["links"]
	if links:
		gsearch_results[query] = links[0]
		return links[0]

def get_wname(name):
	wname = name.lower().replace(" ", "-").replace("'", "").replace(",", "").replace("’", "").replace("?", "").replace("!", "")
	return wname

async def clink(site, name, chapter):
	if site == "-h":
		name = get_wname(name)
		link = "https://hentaidexy.com/reads/" + name + "/chapter-" + chapter
	elif site == "-mc":
		name = get_wname(name)
		link = "https://manhwaclub.net/manga/" + name
		link = get_link(link) + "chapter-" + chapter
	elif site == "-mh":
		name = get_wname(name)
		link = "https://manhwahentai.me/webtoon/" + name
		link = get_link(link) + "chapter-" + chapter
	elif site == "-ws":
		name = get_wname(name)
		link = "https://webtoonscan.com/manhwa/" + name + "/" + chapter
	elif site == "-m":
		name = get_wname(name)
		link = "https://manhwahub.net/webtoon/" + name
		link = get_link(link, cloud=True) + "/chapter-" + chapter
	elif site == "-18":
		name = get_wname(name)
		link = "https://manhwa18.cc/webtoon/" + name + "/chapter-" + chapter
	elif site == "-t":
		name = get_wname(name)
		link = "https://toonily.com/webtoon/" + name
		link = get_link(link, cloud=True) + "chapter-" + chapter
	elif site == "-3z":
		link = await gsearch(name, site=site)
		link = link + "chapter-" + chapter
	elif site == "-20":
		link = await gsearch(name, site=site)
		link = link + "chapter-" + chapter
	elif site == "-t6":
		name = get_wname(name)
		link = "https://toon69.com/manga/" + name 
		link = get_link(link, cloud=True) + "chapter-" + chapter
	return link

def iargs(site):
	class_ = "wp-manga-chapter-img"
	src = "src"
	if site.strip() == "-m":
		class_ = "chapter-img img-responsive"
	elif site.strip() == "-18":
		class_ = re.compile("p*")
	return dict(class_=class_, src=src)
	
		
@app.on_message(filters.user(SUDOS) & filters.regex("^/uws( -thumb)? (-fpdf)? ?(.*)"))
async def _uws(bot, event):
	xx = await event.reply("`Processing ...`")
	is_thumb = event.matches[0].group(1)
	use_fpdf = event.matches[0].group(2)
	input_str = event.matches[0].group(3)
	splited = input_str.split()
	if not input_str or len(splited) < 2:
		await xx.edit("`Sorry, invalid syntax.`")
		await asyncio.sleep(8)
		await xx.delete()
		await event.delete()
		return
	pnames = get_names()
	if input_str.strip().startswith("-"):
		site = splited[0]
		name = pnames[int(splited[1])]
		chapter = splited[2]
		try:
			link = await clink(site, name, chapter)
			args = iargs(site)
			pdfname = f"""Ch - {chapter.replace("-", ".")} {name.title().replace("'S", "'s").replace("’S", "’s")} @Adult_Mangas.pdf"""
			file = await post_ws(link, pdfname, **args, fpdf=bool(use_fpdf))
			await app.send_document(-1001783376856, file, thumb="thumb.jpg" if is_thumb else None)
			os.remove(pdfname)
		except Exception as e:
			await xx.edit(f"**Something Went Wrong❗**\n\n`{type(e).__name__}: {e}`")
			await asyncio.sleep(8)
			await xx.delete()
			await event.delete()
			return
		await xx.edit(f"**Successfully uploaded** [{name.title()}]({link})")
		await asyncio.sleep(8)
		await xx.delete()
		await event.delete()
	else:
		name = pnames[int(splited[0])]
		wname = get_wname(name)
		chapter = splited[1]
		try:
			link = await clink("-18", wname, chapter)
			args = iargs("-18")
			pdfname = f"""Ch - {chapter.replace("-", ".")} {name.title().replace("'S", "'s").replace("’S", "’s")} @Adult_Mangas.pdf"""
			file = await post_ws(link, pdfname, **args, fpdf=bool(use_fpdf))
			await app.send_document(-1001783376856, file, thumb="thumb.jpg" if is_thumb else None)
			os.remove(pdfname)
		except Exception as e:
			await xx.edit(f"**Something Went Wrong❗**\n\n`{type(e).__name__}: {e}`")
			await asyncio.sleep(10)
			await xx.delete()
			await event.delete()
			return 
		await xx.edit(f"**Successfully uploaded** [{name.title()}]({link})")
		await asyncio.sleep(10)
		await xx.delete()
		await event.delete()

@app.on_message(filters.user(SUDOS) & filters.regex("^/read( -thumb)?( -fpdf)? (-h|-mc|-mh|-ws|-m|-18|-t6|-t|-20|-3z) (.*)"))
async def _readp(bot, event):
	xx = await event.reply("`Processing ...`")
	is_thumb = event.matches[0].group(1)
	use_fpdf = event.matches[0].group(2)
	site = event.matches[0].group(3).strip()
	input_str = event.matches[0].group(4)
	splited = input_str.split(" | ")
	if not input_str or len(splited) < 2:
		await xx.edit("`Sorry, invalid synatx.")
		await asyncio.sleep(8)
		await xx.delete()
		return
	name = splited[0]
	chapter = splited[1]
	try:
		link = await clink(site, name, chapter)
		args = iargs(site)
		pdfname = f"""Ch - {chapter.replace("-", ".")} {name.title().replace("'S", "'s").replace("’S", "’s")} @Adult_Mangas.pdf"""
		file = await post_ws(link, pdfname, **args, fpdf=bool(use_fpdf))
		await app.send_document(event.chat.id, file, thumb="thumb.jpg" if is_thumb else None)
		os.remove(file)
	except Exception as e:
		await xx.edit(f"**Something Went Wrong❗**\n\n`{type(e).__name__}: {e}`")
		await asyncio.sleep(8)
		await xx.delete()
		return
	await xx.edit(f"**Successfully uploaded** [{name.title()}]({link})")
	await asyncio.sleep(8)
	await xx.delete()


#UPDATES
def ps_iargs(ps):
	if ps == "Toonily":
		return "-t"
	elif ps == "Manhwa18":
		return "-18"

invitation_links = dict()
async def get_chat_invite_link(chat_id: int):
	if chat_id in invitation_links:
		return invitation_links[chat_id]
	try:
		link = (await bot(functions.channels.GetFullChannelRequest(chat_id))).full_chat.exported_invite.link 
		invitation_links[chat_id] = link 
		return link 
	except:
		return None

async def anext(iteration):
    async for i in iteration: return i

async def iter_chapters(link, ps=None):
	if ps == "Manhwa18":
		bs = get_soup(link)
		urls = list()
		for item in bs.find("div", "panel-manga-chapter wleft").find_all("a"):
			yield urljoin("https://manhwa18.cc/", item["href"])
	
	elif ps == "Toonily":
		bs = get_soup(link)
		urls = dict()
		for item in bs.find_all("li", "wp-manga-chapter"):
			yield item.a["href"]
	
	else:
		raise ValueError 
chapter_log_msg = """
<strong><i>#New_Chapter</strong></i>
<i>{} - {}</i>
"""
async def update_manhwas():
	ps_dict = dict()
	
	for sub in db.find({"msub": {"$exists": 1}}):
		ps = sub["msub"]
		if ps not in ps_dict:
			updates = await updates_from_ps(ps)
			ps_dict[ps] = updates 
	
	for ps in ps_dict:
		logger.info(f"\n»Starting Feed For {ps}...")
		updates = ps_dict[ps]
		for sub in db.find({"msub": ps}):
			link = sub["link"]
			if link not in updates:
				continue 
			chat = sub["chat"]
			title = sub["title"]
			last_chapter = sub["last_chapter"]
			if last_chapter == updates.get(link):
				continue

			logger.info(f"\n»{ps} Feed: Updating {title}")
			new_chapters = list()
			async for i in iter_chapters(link, ps):
				if i == last_chapter: 
					break 
				new_chapters.append(i)
			new_chapters.reverse()

			for ch_link in new_chapters:
				logger.info(f"\n»{title} ({ps}) Feed: Updating {ch_link}")
				ch = (ch_link.split("/")[-1] or ch_link.split("/")[-2]).replace("chapter-", "").replace("-", ".").strip()
				pdfname = f"Ch - {ch} {title} @Adult_Mangas.pdf"
				try:
					file = await post_ws(ch_link, pdfname, **iargs(ps_iargs(ps)), fpdf=True)
					msg = await app.send_document(chat, file)
					os.remove(file)
					sub["last_chapter"] = ch_link
					db.update_one({"msub": ps, "link": link}, {"$set": sub})
					await app.send_message(-1001848617769, chapter_log_msg.format(title, ch))
				except Exception as e:
					logger.info(f"\n{title} ({ps}) Feed: {ch_link}: Error: {e}")
					await app.send_message(LOG_CHAT, f"<b>{title} ({ps}) Feed:</b> {ch_link}\n\n**Something Went Wrong❗**\n\n`{type(e).__name__}: {e}`")
		logger.info(f"\n»Completed Run For {ps}")

scheduler = AsyncIOScheduler()
scheduler.add_job(update_manhwas, "interval", minutes=5)
scheduler.start()
