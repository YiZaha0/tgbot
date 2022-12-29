import re
import os
import random
import requests
import time
import asyncio
import zipfile

from html_telegraph_poster import TelegraphPoster
from html_telegraph_poster.errors import TelegraphError
from asyncio import sleep
from telethon import events 
from natsort import natsorted
from pyrogram import filters
from pyrogram.enums import ParseMode
from .utils.auws import fld2pdf, nhentai, create_pdf, images_to_pdf, session

from . import *

async def post_to_telegraph(page_title, html_format_content):
    post_client = TelegraphPoster(use_api=True, telegraph_api_url='https://api.graph.org')
    auth_name = "@Adult_Mangas"
    post_client.create_api_token(auth_name)
    try:
    	post_page = post_client.post(
        title=page_title,
        author=auth_name,
        author_url="https://t.me/Adult_Mangas",
        text=html_format_content)
    except TelegraphError:
    	return
    return post_page["url"]

async def _to_pdf(images: list, filename: str, code: str, alsocbz: bool = False, referer=None):
	pdf_path = os.path.join("./cache/nhentai", filename + ".pdf")
	cbz_path = os.path.join("./cache/nhentai", filename + ".cbz")
	if os.path.exists(pdf_path):
		return ((pdf_path, cbz_path) if alsocbz else pdf_path)
	os.path.isdir("cache/nhentai") or os.mkdir("cache/nhentai")
	dir = os.path.join("./cache/nhentai", code)
	os.path.isdir(dir) or os.mkdir(dir)
	process = list()
	n = 0
	image_list = list()
	headers = dict(session.headers)
	headers["Referer"] = referer
	for i in images:
		name = os.path.join(dir, i.split("/")[-1])
		n += 1
		process.append(req_download(i, filename=name, headers=headers))
		image_list.append(name)
	await asyncio.gather(*process)
	try:
		fld2pdf(image_list, pdf_path.replace(".pdf", ""))
	except:
		images_to_pdf(pdf_path, image_list)
	with zipfile.ZipFile(cbz_path, "w") as cbz:
		for img in image_list:
			cbz.write(img, compress_type=zipfile.ZIP_DEFLATED)
	shutil.rmtree(dir)
	return ((pdf_path, cbz_path) if alsocbz else pdf_path)

@app.on_message(filters.regex("[!/]nh(?: |$)(.*)") & filters.user(SUDOS))
async def _(bot, event):
	chat = -1001765257929
	m = await event.reply("`Processing ...`")
	input_str = event.matches[0].group(1)
	if not input_str:
		return await m.edit("`Give any Doujin to upload for...`")
	try:
		doujin = nhentai(input_str)
	except Exception as e:
		await m.edit(f"**Error :** `{e}`")
		return
	msg = ""
	imgs =  "".join(f"<img src='{url}'/>" for url in doujin.images)
	title = doujin.title
	nn = title.split("|")
	pdfname = nn[0].strip() + " @Adult_Mangas"
	pdfname = pdfname.replace("/", "|")
	graph_link = await post_to_telegraph(title, imgs)
	msg += f"[{title}]({graph_link})\n"
	msg += f"\n➤ **Code :** {doujin.code}"
	if doujin.categories:
		msg += "\n➤ **Type : **"
		msg += " ".join(natsorted(doujin.categories))
	if doujin.parodies:
		msg += "\n➤ **Parodies : **"
		msg += " ".join(natsorted(doujin.parodies))
	if doujin.artists:
		msg += "\n➤ **Artists : **"
		msg += " ".join(natsorted(doujin.artists))
	if doujin.languages:
		msg += "\n➤ **Languages : **"
		msg += " ".join(natsorted(doujin.languages))
	msg += f"\n➤ **Pages :** {doujin.pages}"
	if doujin.tags:
		msg += "\n➤ **Tags : **"
		msg += " ".join(natsorted(doujin.tags))
	file = await _to_pdf(doujin.images, pdfname, doujin.code, referer=doujin.url)
	graph_post = msg.split("\n")[0]
	await m.edit(graph_post)
	graph_link = await post_to_telegraph(title, imgs)
	graph_link = graph_link or doujin.read_url
	graph_post = f"[{title}]({graph_link})"
	msg = msg.replace(msg.split("\n")[0], graph_post)
	temp_msg = await bot.send_message(-1001783376856, graph_link)
	mess = await bot.send_message(chat, msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
	await app.send_document(chat, file, caption="**PDF VIEW**")
	await app.send_cached_media(chat, "CAADAQADRwIAArtf8EeIGkF9Fv05gQI")
	await temp_msg.delete()
	here = f"[{mess.chat.title}]({mess.link})."
	await m.edit(f"<b><i>Done Successfully Sent  in {here}</i></b>")

@app.on_message(filters.regex("^[/!]nhentai(?: |$)(.*)") & ~filters.user([5710896893]))
async def dn_(bot, event):
	m = await event.reply("`Processing...`")
	input_str = event.matches[0].group(1)
	if not input_str:
		return await m.edit("`Sorry, give me any nuclear code first.`")
	try:
		doujin = nhentai(input_str)
	except Exception as e:
		await m.edit(f"**Error :** `{e}`")
		return
	msg = ""
	imgs =  "".join(f"<img src='{url}'/>" for url in doujin.images)
	title = doujin.title
	pdfname = f"{doujin.code}"
	graph_link = await post_to_telegraph(title, imgs)
	graph_link = graph_link or doujin.read_url
	msg += f"[{title}]({graph_link})\n"
	msg += f"\n➤ **Code :** {doujin.code}"
	if doujin.categories:
		msg += "\n➤ **Type : **"
		msg += " ".join(natsorted(doujin.categories))
	if doujin.parodies:
		msg += "\n➤ **Parodies : **"
		msg += " ".join(natsorted(doujin.parodies))
	if doujin.artists:
		msg += "\n➤ **Artists : **"
		msg += " ".join(natsorted(doujin.artists))
	if doujin.languages:
		msg += "\n➤ **Languages : **"
		msg += " ".join(natsorted(doujin.languages))
	msg += f"\n➤ **Pages :** {doujin.pages}"
	if doujin.tags:
		msg += "\n➤ **Tags : **"
		msg += " ".join(natsorted(doujin.tags))
	await m.edit(f"`Wait a bit... Downloading` [{title}]({doujin.url})")
	pdf, cbz = await _to_pdf(doujin.images, pdfname, doujin.code, alsocbz=True, referer=doujin.url)
	await bot.send_message(event.chat.id, msg, parse_mode=ParseMode.MARKDOWN)
	await asyncio.gather(app.send_document(event.chat.id, pdf), app.send_document(event.chat.id, cbz))
	await asyncio.gather(m.delete(), bot.send_message(-1001568226560, f"[{title}]({doujin.url})\n\nSuccessfully sent to {event.from_user.mention}"))

@app.on_message(filters.regex("^[/!]dn(?: |$)(.*)") & filters.user(SUDOS))
async def telegraphNhentai(bot, event):
	m = await event.reply("`Processing...`")
	input_str = event.matches[0].group(1)
	if not input_str:
		return await m.edit("`Sorry, give me any nuclear code first.`") and await asyncio.sleep(10) and await asyncio.gather(m.delete(), event.delete())
	try:
		doujin = nhentai(input_str)
	except Exception as e:
		await m.edit(f"**Error :** `{e}`") and await asyncio.sleep(10) and await asyncio.gather(m.delete(), event.delete())
		return
	msg = ""
	imgs =  "".join(f"<img src='{url}'/>" for url in doujin.images)
	title = doujin.title
	graph_link = await post_to_telegraph(title, imgs)
	msg += f"[{title}]({graph_link})\n"
	msg += f"\n➤ **Code :** {doujin.code}"
	if doujin.categories:
		msg += "\n➤ **Type : **"
		msg += " ".join(natsorted(doujin.categories))
	if doujin.parodies:
		msg += "\n➤ **Parodies : **"
		msg += " ".join(natsorted(doujin.parodies))
	if doujin.artists:
		msg += "\n➤ **Artists : **"
		msg += " ".join(natsorted(doujin.artists))
	if doujin.languages:
		msg += "\n➤ **Languages : **"
		msg += " ".join(natsorted(doujin.languages))
	msg += f"\n➤ **Pages :** {doujin.pages}"
	if doujin.tags:
		msg += "\n➤ **Tags : **"
		msg += " ".join(natsorted(doujin.tags))
	await m.edit(f"`Wait a bit... Processing` [{title}]({doujin.url})")
	graph_post = msg.split("\n")[0]
	graph_link = await post_to_telegraph(title, imgs)
	graph_link = graph_link or doujin.read_url
	graph_post = f"[{title}]({graph_link})"
	msg = msg.replace(msg.split("\n")[0].strip(), graph_post)
	await asyncio.gather(m.edit(msg, parse_mode=ParseMode.MARKDOWN))
