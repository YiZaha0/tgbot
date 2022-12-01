from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto 
from .utils.ani import get_anime_manga, searchanilist
from . import *

@app.on_message(filters.command("anime") & (filters.channel | ~filters.channel))
async def anime_(client, event):
	text = event.text.split(" ", maxsplit=1)
	if len(text) == 1:
		k = await event.reply("`What should i do? Give me a query to search for.`")
		await asyncio.sleep(8)
		await k.delete()
		return
	results = (await searchanilist(text[1], manga=False))[0]
	if not results:
		k = await event.reply("`No result found for the given query.`")
		await asyncio.sleep(8)
		await k.delete()
		return
	buttons = []
	for result in results:
		name = result["title"].get("english") or result["title"].get("romaji")
		id = str(result["id"])
		if not get_db(id, cn="Adb"):
			add_db(id, result["title"].get("native") or result["title"].get("romaji"), cn="Adb")
		buttons.append([InlineKeyboardButton(name, f"anime_{id}")])
	await event.reply(f"Search results for `{text[1]}`", reply_markup=InlineKeyboardMarkup(buttons))
	if not event.from_user:
		await event.delete()

@app.on_message(filters.command("manga") & (filters.channel | ~filters.channel))
async def manga_(client, event):
	text = event.text.split(" ", maxsplit=1)
	if len(text) == 1:
		k = await event.reply("`What should i do? Give me a query to search for.`")
		await asyncio.sleep(8)
		await k.delete()
		return
	results = (await searchanilist(text[1], manga=True))[0]
	if not results:
		k = await event.reply("`No result found for the given query.`")
		await asyncio.sleep(8)
		await k.delete()
		return
	buttons = []
	for result in results:
		name = result["title"].get("english") or result["title"].get("romaji")
		id = str(result["id"])
		if not get_db(id, cn="Adb"):
			add_db(id, result["title"].get("native") or result["title"].get("romaji"), cn="Adb")
		buttons.append([InlineKeyboardButton(name, f"manga_{id}")])
	await event.reply(f"Search results for `{text[1]}`", reply_markup=InlineKeyboardMarkup(buttons))
	if not event.from_user:
		await event.delete()

@app.on_callback_query(filters.regex(r"manga_(.*)"))
async def manga_data(client, event):
	Adb = mongodb["Adb"]
	manga_id = event.matches[0].group(1)
	message = event.message
	manga = get_db(manga_id, cn="Adb")
	if not manga:
		return await event.answer("This is an old button. Please redo the command.")
	await event.answer("Processing...")
	text, image, reply_markup = await get_anime_manga(manga, "anime_manga", event.from_user.id)
	image_path = "./plugins/utils/anilist_img-{anime_id}.jpg"
	os.path.exists(image_path) or await req_download(image, filename=image_path)
	if message.photo:
		media = InputMediaPhoto(image_path, caption=text)
		await event.edit_message_media(media, reply_markup=reply_markup)
		return
	await message.reply_photo(image_path, caption=text, reply_markup=reply_markup, quote=False)
	await message.delete()

@app.on_callback_query(filters.regex(r"anime_(.*)"))
async def anime_data(client, event):
	Adb = mongodb["Adb"]
	anime_id = event.matches[0].group(1)
	anime = get_db(anime_id, cn="Adb")
	if not anime:
		return await event.answer("This is an old button. Please redo the command.")
	message = event.message
	await event.answer("Processing...")
	text, image, reply_markup = await get_anime_manga(anime, "anime_anime", event.from_user.id)
	image_path = "./plugins/utils/anilist_img-{anime_id}.jpg"
	os.path.exists(image_path) or await req_download(image, filename=image_path)
	if message.photo:
		media = InputMediaPhoto(image_path, caption=text)
		await event.edit_message_media(media)
		return
	await message.reply_photo(image_path, caption=text, reply_markup=reply_markup, quote=False)
	await message.delete()

