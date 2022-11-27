import requests
import datetime
import asyncio
import cloudscraper

from search_engine_parser import GoogleSearch
from pyrogram import filters, types
from telethon import functions
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
<i>→{}
→Chapter {}</i>
"""
async def manhwa_updates():
	ps_updates = dict()
	for sub in db.find({"msub": {"$exists": 1}}):
		ps = sub["msub"]
		if ps not in ps_updates:
			updates = await updates_from_ps(ps)
			ps_updates[ps] = updates 
	
	manhwas_updates = dict()
	for ps, updates in ps_updates.items():
		if not manhwas_updates.get(ps):
			manhwas_updates[ps] = dict()
		
		for sub in db.find({"msub": ps}):
			link = sub["link"]
			last_chapter = sub["last_chapter"]
			
			if not updates.get(link) or updates.get(link) == last_chapter:
				continue
			
			new_chapters = list()
			
			async for i in iter_chapters(link, ps):
				if i == last_chapter:
					break 
				new_chapters.append(i) 
			new_chapters.reverse()
			
			manhwas_updates[ps][link] = new_chapters 
	
	return manhwas_updates

async def update_manhwas():
	updates = await manhwa_updates()
	await asyncio.sleep(5)
	
	for ps, update in updates.items():
		print(f"»Starting Updates Run for {ps}")
		await asyncio.sleep(1)
		
		for link, new_chapters in update.items():
			sub = db.find_one({"msub": ps, "link": link})
			title = sub["title"]
			chat = sub["chat"]
			print(f"»{ps} Feed: Updates for {title}\n→{new_chapters}")
			#to get manhwa channel link
			reply_markup = list()
			chat_invite = await get_chat_invite_link(chat)
			if chat_invite:
				reply_markup.append([types.InlineKeyboardButton("Read Here", url=chat_invite)])
				reply_markup = types.InlineKeyboardMarkup(reply_markup)
			
			for ch_link in new_chapters:
				if link in Errors:
					break
				ch = (ch_link.split("/")[-1] or ch_link.split("/")[-2]).split("-")[-1]
				ch = ch.replace("-", ".", 1).replace("-", "", 1).replace("-", " ")
				pdfname = f"Ch - {ch} {title} @Adult_Mangas.pdf"
				try:
					chapter_file = await post_ws(ch_link, pdfname, **iargs(ps_iargs(ps)), fpdf=True)
				except Exception as e:
					not os.path.exists(pdfname) or os.remove(pdfname)
					print(f"»{ps} Feed: Got Error while updating {ch_link}\n→{e}")
					break
				await asyncio.sleep(1)
				try:
					sub["last_chapter"] = ch_link
					chapter_msg = await app.send_document(chat, chapter_file, protect_content=True)
					os.remove(chapter_file)
					await app.send_message(-1001848617769, chapter_log_msg.format(title, ch), reply_markup=reply_markup)
					db.update_one({"msub": ps, "link": link}, {"$set": sub})
					await asyncio.sleep(2.5)
				except Exception as e:
					print(f"»{ps} Feed: Got Error while updating {ch_link}\n→{e}") 

		print(f"»Completed Updates Run for {ps}")

async def manhwa_updater():
    while True:
        wait_time = 300
        try:
            start = datetime.datetime.now()
            await update_manhwas()
            end = datetime.datetime.now() - start
            wait_time = max((dt.timedelta(seconds=sleep_time) - elapsed).total_seconds(), 0)
            print(f'Time elapsed updating manhwas: {elapsed}, waiting for {wait_time}')
        except BaseException as e:
            print(f'»Got Error While Updating Manhwas: {e}')
        if wait_time:
            await asyncio.sleep(wait_time) 
