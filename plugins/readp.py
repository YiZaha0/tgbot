
import requests
import datetime
import asyncio
import cloudscraper

from search_engine_parser import GoogleSearch
from pyrogram import filters, types
from telethon import functions
from .utils.auws import *
from .manga import dl_mgn_thumb
from . import *

chapter_log_msg = """
<strong><i>#New_Chapter</strong></i>
<i>→{}
→Chapter {}</i>
"""

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
		name = get_wname(name)
		link = "https://hentai3z.com/manga/" + name
		link = get_link(link, cloud=True) + "chapter-" + chapter
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
@app.on_message(filters.command("new_ch") & filters.user(SUDOS))
async def upost_(_, update):
	status = await update.reply("`Processing`")
	try:
		cmd, text = update.text.split(" ", 1)
	except:
		return await status.edit("`Invalid syntax for upost.`")
	text = text.split(" | ")
	if len(text) in (1, 4):
		return await status.edit("`Invalid syntax for upost.`")
	title = text[0]
	ch = text[1]
	chat = text[2].strip() if len(text) == 3 else None
	try:
		chat = int(chat)
	except:
		await status.edit("`Invalid chat_id for upost.`")

	reply_markup = []
	upost_text = chapter_log_msg.format(title, ch)
	if chat:
		chat_link = await get_chat_invite_link(chat)
		if chat_link:
			reply_markup.append([types.InlineKeyboardButton("Read Here", url=chat_link)])
			reply_markup = types.InlineKeyboardMarkup(reply_markup)
		else:
			await status.edit("Couldn't get invitation link from chat, proceeding without read button.")
			await asyncio.sleep(3)
	
	upost_msg = await app.send_message(-1001848617769, upost_text, reply_markup=reply_markup)
	await status.edit(f"Successfully sent chapter log message in [{upost_msg.chat.title}]({upost_msg.link}).")

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

async def manhwa_updates():
	ps_updates = dict()
	sub_chats = dict()
	for sub in db.find({"msub": {"$exists": 1}}):
		ps = sub["msub"]
		link = sub["link"]
		chat = sub["chat"]
		if link not in sub_chats:
			sub_chats[link] = list()
		sub_chats[link].append(chat)
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
			if link in manhwas_updates:
 				continue

			new_chapters = list()
			
			async for i in iter_chapters_ps(link, ps):
				if i == last_chapter:
					break 
				new_chapters.append(i) 
			new_chapters.reverse()

			if new_chapters:
				manhwas_updates[ps][link] = new_chapters 
	
	return manhwas_updates, sub_chats

async def update_manhwas():
	updates, sub_chats = await manhwa_updates()
	await asyncio.sleep(5)
	
	for ps, update in updates.items():
		logger.info(f"»Starting Updates Run for {ps}")
		await asyncio.sleep(1)
		
		for link, new_chapters in update.items():
			sub = db.find_one({"msub": ps, "link": link})
			title = sub["title"].replace("’", "'")
			chats = sub_chats[link]
			logger.info(f"»{ps} Feed: Updates for {title}\n→{new_chapters}")
			
			for ch_link in new_chapters:
				ch = (ch_link.split("/")[-1] or ch_link.split("/")[-2]).replace("chapter-", "").strip()
				ch = ch.replace("-", ".", 1).replace("-", "", 1).replace("-", " ")
				pdfname = f"Ch - {ch} {title} @Adult_Mangas.pdf"
				thumb = None
				try:
					if ps == "Manganato":
						manga_id = link.split("/")[-1]
						manga = Minfo(manga_id)
						thumb = await dl_mgn_thumb(manga)
						pdfname = pdfname.replace(" @Adult_Mangas.pdf", "")
						chapter_file = await dl_chapter(ch_link, pdfname, "pdf")
					else:
						chapter_file = await post_ws(ch_link, pdfname, **iargs(ps_iargs(ps)), fpdf=True)
				except Exception as e:
					not os.path.exists(pdfname) or os.remove(pdfname)
					logger.info(f"»{ps} Feed: Got Error while updating {ch_link}\n→{e}")
					break
					
				await asyncio.sleep(3)
				
				reply_markup = list()
				for chat in chats:
					chat_invite = await get_chat_invite_link(chat)
					if chat_invite:
						reply_markup.append([types.InlineKeyboardButton("Read Here", url=chat_invite)])
						reply_markup = types.InlineKeyboardMarkup(reply_markup)
						
					try:
						await app.send_document(chat, chapter_file, thumb=thumb, protect_content=True)
					except Exception as e:
						logger.info(f"»{ps} Feed: Got Error while sending {ch_link} in {chat}\n→{e}")
						
					if ps != "Manganato":
						await app.send_message(-1001848617769, chapter_log_msg.format(title, ch), reply_markup=reply_markup)

				os.remove(chapter_file)
				not thumb or os.remove(thumb)
				for _sub in db.find({"msub": ps, "link": link}):
					_sub["last_chapter"] = ch_link
					db.update_one({"_id": _sub["_id"]}, {"$set": _sub})					
				await asyncio.sleep(2.5)

		logger.info(f"»Completed Updates Run for {ps}")

async def manhwa_updater():
    while True:
        wait_time = 300
        try:
            start = datetime.datetime.now()
            await update_manhwas()
            elapsed = datetime.datetime.now() - start
            wait_time = max((datetime.timedelta(seconds=wait_time) - elapsed).total_seconds(), 0)
            logger.info(f'Time elapsed updating manhwas: {elapsed}, waiting for {wait_time}')
        except BaseException as e:
            logger.info(f'»Got Error While Updating Manhwas: {e}')
        if wait_time:
            await asyncio.sleep(wait_time) 
