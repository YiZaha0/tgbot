from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto 
from bs4 import BeautifulSoup 
from .utils.auws import Minfo, dl_chapter

from . import *

CACHE_CHAT = -1001590019547

@app.on_message(filters.regex("^/getmanga ?(.*)") & filters.user(SUDOS+[5591954930]))
async def getmanga_(bot, update):
	query = update.matches[0].group(1)
	if not query:
		return await update.reply("`What should i do? Give me a query to search for.`")
	m = await update.reply("`Searching...`")
	results = requests.post("https://manganato.com/getstorysearchjson", data={"searchword": query}).json()
	results = results["searchlist"]
	if not results:
		return await m.edit("`No result found for the given query.`")
	data = dict()
	regex = re.compile(r"<span .*?>(.+?)</span>")
	for item in results:
		name = item["name"]
		while "</span>" in name:
			name = re.sub(regex, r"\1", name)
		data[name.title().replace("'S", "'s")] = item["url_story"]
	buttons = []
	for d in data:
		title = d
		url = data[d]
		manga_id = "manga-" + "".join(re.findall("manga-(.*)", url))
		buttons.append([InlineKeyboardButton(title, f"mgn_{manga_id}")])
	await m.edit(f"Search results for `{query}`", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"mgn_(.*)"), group=10)
async def getmanga_data(bot, update):
	await update.answer()
	id = update.matches[0].group(1)
	manga = Minfo(id)
	chapters = list(manga.chapters.keys())[-1]
	authors = ", ".join(sorted(manga.authors))
	genres = ", ".join(sorted(manga.genres))
	description = post_telegraph(manga.title.strip(), manga.description, "@UselessAf_Bot", author_url="https://t.me/UselessAf_Bot")
	caption = f"<b>{manga.title}</b>\n\n<b>Alternative(s) :</b> {manga.alternatives}\n\n<b>ID :</b> <code>{manga.id}</code>\n<b>Views :</b> {manga.views}\n<b>Status :</b> {manga.status}\n<b>Updated :</b> {manga.updated}\n<b>Chapters :</b> {chapters}\n<b>Authors :</b> {authors}\n<b>Genres :</b> {genres}\n\n<b>[Synopsis]({description})</b>"
	await app.send_photo(update.message.chat.id, manga.poster_url, caption=caption)
	await update.message.delete()

@app.on_message(filters.command("mread") & filters.user(SUDOS+[5591954930]))
async def read_manga(bot, update):
	try:
		text = update.text.split(" ", 1)[1]
	except:
		return await update.reply("`Give manga Id and chapter No.`")

	is_thumb = True if "-thumb" in text else False 
	nelo = True if "-nelo" in text else False 
	mode = "pdf" if "-pdf" in text else "cbz"
	flags = ("-thumb", "-nelo", "-pdf", "-protect")
	for _f in flags:
		text = text.replace(_f, "").strip()

	text = text.split(" ", 1)
	if len(text) != 2:
		return await update.reply("`Give manga Id and chapter No.`")
		
	manga_id = text[0]
	chapter_no = text[1]
	try:
		manga = Minfo(manga_id, nelo=nelo)
	except BaseException:
		return await update.reply("`Manga ID not found.`")
	try:
		chapter_url = manga.chapters[chapter_no]
	except KeyError:
		return await update.reply("`Chapter No Invalid/Not Found.`")
		
	mm = await update.reply("`Processing...`")
	data = "nelo-" if nelo else ""
	data += manga.id + "-ch-" + chapter_no
	is_chapter = get_db(data, cn="CACHE")
	ch = check(chapter_no)
	file_name = f"Ch - {ch} {manga.title}"
	if is_thumb:
		thumb = await dl_mgn_thumb(manga)
	else:
		thumb = None
	try:
		file = await dl_chapter(chapter_url, file_name, mode)
		K = await app.send_document(update.chat.id, file, caption=f"**{manga.title}\nChapter - {ch}**", thumb=thumb)
		await mm.delete()
		os.remove(file)
	except Exception as e:
		await mm.edit(f"**Something Went Wrong❗**\n\n`{e.__class__.__name__} : {e}`")

@app.on_message(filters.command("mbulk") & filters.user(SUDOS+[5591954930]))
async def bulkmanga(bot, update):
	try:
		text = update.text.split(" ", 1)[1]
	except:
		return await update.reply("`Give manga Id.`")
		
	is_thumb = True if "-thumb" in text else False 
	nelo = True if "-nelo" in text else False 
	mode = "pdf" if "-pdf" in text else "cbz"
	protect = True if "-protect" in text else False
	flags = ("-thumb", "-nelo", "-pdf", "-protect")
	for _f in flags:
		text = text.replace(_f, "").strip()
	
	manga_id = text 
	chat = update.chat.id
	if " | " in text:
		splited = text.split(" | ")
		manga_id = splited[0].strip()
		chat = splited[1].strip()
		
	try:
		manga = Minfo(manga_id, nelo=nelo)
	except:
		return await update.reply("`Invalid Manga ID`")

	m = await update.reply("`Processing...`")
	
	if is_thumb:
		thumb = await dl_mgn_thumb(manga)
	else:
		thumb = None 
	
	ch_msg = None 
	_edited = False 
	here = None
	for ch in manga.chapters:
		if ch_msg and not _edited:
			here = await get_chat_link_from_msg(ch_msg)
			await m.edit(f"Bulk uploading {list(manga.chapters)[-1]} chapters of [{manga.title}]({manga.url}) in [here.]({here})")
			_edited = True
		try:
			url = manga.chapters[ch]
			ch = check(ch)
			title = f"Ch - {ch} {manga.title}"
			file = await dl_chapter(url, title, mode)
			ch_msg = await app.send_document(int(chat), file, thumb=thumb, protect_content=protect)
			os.remove(file)
		except Exception as e:
			await m.edit(f"**Something Went Wrong❗**\n\n`{e.__class__.__name__} : {e}`")
			return
		await asyncio.sleep(3)

	if thumb:
		os.remove(thumb)
	
	await m.edit(f"Successfully bulk uploaded {list(manga.chapters)[-1]} chapters of [{manga.title}]({manga.url}) in [here.]({here})")
	
async def get_chat_link_from_msg(message):
	if message.chat.username:
		return f"https://t.me/{message.chat.username}"
		
	elif message.chat.type._value_ == "private":
		 return f"tg://user?id={message.chat.id}"
		
	elif message.chat.invite_link:
		return message.chat.invite_link
	
	else:
		return message.link.replace("-100", "")

async def dl_mgn_thumb(manga=None, url=None):
	try:
		if url:
			thumb = (await req_download(url))[0]
		elif manga:
			thumb = (await req_download(manga.poster_url))[0]
		else:
			raise ValueError
	except:
		thumb = None 
	return thumb
