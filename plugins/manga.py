from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto 
from bs4 import BeautifulSoup 
from .utils.auws import Minfo, dl_chapter

from . import *

CACHE_CHAT = -1001590019547

@app.on_message(filters.regex("^/getmanga ?(.*)"))
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

@app.on_message(filters.command("mread"))
async def read_manga(bot, update):
	text = update.text.split(" ")
	if not len(text) == 3:
		return await update.reply("`Give manga Id and chapter No.`")
	manga_id = text[1]
	chapter_no = text[2]
	try:
		manga = Minfo(manga_id, nelo=True)
	except BaseException:
		return await update.reply("`Manga ID not found.`")
	try:
		chapter_url = manga.chapters[chapter_no]
	except KeyError:
		return await update.reply("`Chapter No Invalid/Not Found.`")
	mm = await update.reply("`Processing...`")
	data = manga.id + "-ch-" + chapter_no
	is_chapter = get_db(data, cn="CACHE")
	if not is_chapter:
		chapter_no = ech(chapter_no)
		file_name = f"[Ch {chapter_no}] {manga.title}"
		try:
			file = await dl_chapter(chapter_url, file_name, "cbz")
			K = await app.send_document(CACHE_CHAT, file, caption=f"**{manga.title} - Chapter {chapter_no}**")
			await K.copy(update.chat.id, caption=K.caption.markdown)
			await mm.delete()
			add_db(data, K.document.file_id, cn="CACHE")
			os.remove(file)
		except Exception as e:
			await mm.edit(f"**Something Went Wrong❗**\n\n`{e}`")
	if is_chapter:
		await app.send_cached_media(update.chat.id, is_chapter, caption=f"**{manga.title} - Chapter {chapter_no}**")
		await mm.delete()

@app.on_message(filters.regex("^/mbulk( -t)? (-nelo)? ?(.*)") & filters.user(SUDOS))
async def bulkmanga(bot, update):
	is_thumb = update.matches[0].group(1)
	is_nelo = update.matches[0].group(2)
	input_str = update.matches[0].group(3)
	if not input_str:
		return await update.reply("`Sorry, invalid syntax`")
	args = dict()
	splited = input_str.split(" | ")
	if len(splited) == 2:
		manga_id = splited[0].strip()
		chat = splited[1].strip()
	else:
		manga_id = input_str.strip()
		chat = update.chat.id
	try:
		if is_nelo:
			manga = Minfo(manga_id, nelo=True)
		else:
			manga = Minfo(manga_id, nelo=False)
	except:
		return await update.reply("`Invalid Manga ID`")
	m = await update.reply("`Processing...`")
	if is_thumb:
		args["thumb"] = (await fast_download(manga.poster_url))[0]
	for ch in manga.chapters:
		try:
			url = manga.chapters[ch]
			ch = ech(ch)
			title = f"[CH - {ch}] {manga.title}"
			file = await dl_chapter(url, title, "cbz")
			await app.send_document(int(chat), file, **args)
			os.remove(file)
		except Exception as err:
			await m.edit(f"**Something Went Wrong❗**\n\n`{err}`")
			return
	if args:
		os.remove(args["thumb"])
	await m.edit(f"Bulk uploaded `{manga.title}`")

def ech(value):
	value = str(value)
	if len(value) == 1:
		return f"0{value}"
	return value
