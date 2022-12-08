from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from natsort import natsorted
from .nhentai import post_to_telegraph
from . import *


Api = "https://hanime-api.vercel.app"
@app.on_message(filters.command("hentai"))
async def search_hentai(bot, update):
	text = update.text.split(" ", maxsplit=1)
	if len(text) == 1:
		return await update.reply("`What should i do? Give me a query to search for.`")
	results = requests.get(f"{Api}/search?query={text[1]}&page=0").json()
	if not results["response"]:
		return await update.reply("`No result found for the given query.`")
	buttons = []
	for response in results["response"]:
		name = response["name"]
		slug = response["id"]
		buttons.append([InlineKeyboardButton(name, f"if_{slug}")])
	await update.reply(f"Search results for `{text[1]}`", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"if(.*)"))
async def info_hentai(bot, update):
	data = update.data.split("_")
	query = data[-1]
	buttons = [[InlineKeyboardButton("Download", f"hl_{query}")], [InlineKeyboardButton("❌ Close", "close")]]
	if data[0].strip() == "ife":
		await update.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
		return
	message = update.message
	result = requests.get(f"{Api}/details?id={query}").json()
	name = result["name"]
	rd = result["released_date"].replace(" ", "-")
	censor = "Censored" if result["is_censored"] else "Uncensored"
	brand = result["brand"]
	tags = ", ".join(natsorted(result["tags"]))
	ides = await post_to_telegraph(name, result["description"])
	des = f"<a href='{ides}'><b>Read More</b></a>"
	poster_url = result["poster"]
	caption = f"<b>{name}</b> [{censor}]\n\n<b>»Release Date -</b> <i>{rd}</i>\n<b>»Studio -</b> <i>{brand}</i>\n<b>»Genres -</b> <i>{tags}</i>\n\n{des}"
	if data[0].strip() == "ifec":
		await update.edit_message_caption(caption, reply_markup=InlineKeyboardMarkup(buttons))
		return
	try:
		await message.reply_photo(poster_url, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
	except BaseException:
		file = await req_download(poster_url)
		await message.reply_photo(file[0], caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
		os.remove(file[0])
	await update.answer()
		
@app.on_callback_query(filters.regex(r"hl_(.*)"))
async def link_hentai(bot, update):
	query = update.matches[0].group(1)
	message = update.message
	result = requests.get(f"{Api}/link?id={query}").json()
	url = result["data"][0]["url"]
	if not url == "":
		url1 = result["data"][0]["url"]
		url2 = result["data"][1]["url"]
		url3 = result["data"][2]["url"]
		buttons = [
			[InlineKeyboardButton("360p", url=f"{url3}"), InlineKeyboardButton("480p", url=f"{url2}")],
			[InlineKeyboardButton("720p", url=f"{url1}")],
			[InlineKeyboardButton("🔙 Back", f"ife_{query}")]
		]
		await message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
	if url == "":
		url1 = result["data"][1]["url"]
		url2 = result["data"][2]["url"]
		url3 = result["data"][3]["url"]
		buttons = [
			[InlineKeyboardButton("360p", url=f"{url3}"), InlineKeyboardButton("480p", url=f"{url2}")],
			[InlineKeyboardButton("720p", url=f"{url1}")],
			[InlineKeyboardButton("🔙 Back", f"ife_{query}")]
		]
		await message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
	await update.answer()

@app.on_callback_query(filters.regex(r"hdl_(.*)"))
async def download_hentai(bot, update):
	query = update.matches[0].group(1)
	is_hentai = get_db(query)
	buttons = [[InlineKeyboardButton("🔙 Back", f"ifec_{query}")]]
	reply_markup = InlineKeyboardMarkup(buttons)
	message = update.message
	cache_chat = -1001568226560
	if is_hentai:
		await message.edit("<code>Uploading File...</code>")
		await bot.copy_message(message.chat.id, cache_chat, is_hentai, caption=f"`{query}.mp4`")
		await message.edit("<code>Upload Completed!</code>", reply_markup=reply_markup)
		return
	result = requests.get(f"{Api}/link?id={query}").json()
	url = result["data"][0]["url"]
	await message.edit(f"<code>Wait a bit... Downloading {query}.mp4 </code>")
	if not is_hentai:
		if not url == "":
			url_dl = result["data"][0]["url"]
		if url == "":
			url_dl = result["data"][1]["url"]
		file = f"{query}.mp4"
		await run_cmd(f"downloadm3u8 -o {file} {url_dl}")
		await message.edit("<code>Now Uploading File...</code>")
		K = await message.reply_document(file, caption=f"`{file}`")
		D = await bot.send_document(cache_chat, K.document.file_id, caption=K.caption.markdown)
		add_db(query, D.id)
		os.remove(file)
		await message.edit("<code>Upload Completed!</code>", reply_markup=reply_markup)
	await update.answer()

@app.on_callback_query(filters.regex(r"close"))
async def close_(bot, update):
	await update.answer()
	await update.message.delete()
