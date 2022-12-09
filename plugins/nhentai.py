import re
import os
import random
import requests
import time
import asyncio

from html_telegraph_poster import TelegraphPoster
from html_telegraph_poster.errors import TelegraphError
from asyncio import sleep
from telethon import events 
from natsort import natsorted
from pyrogram import filters
from pyrogram.enums import ParseMode
from .utils.auws import fld2pdf, nhentai, create_pdf, images_to_pdf

from . import *

async def post_to_telegraph(page_title, html_format_content):
    post_client = TelegraphPoster(use_api=True)
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
    return post_page["url"].replace("telegra.ph", "graph.org")

async def images_to_pdf(images: list, pdfname: str, dir: str = "nhentai"):
	os.path.exists(dir) or os.mkdir(dir)
	process = list()
	n = 0
	image_list = list()
	for i in images:
		name = dir + "/" + i.split("/")[-1]
		n += 1
		await req_download(i, filename=name)
		image_list.append(name)
	path = os.path.join(os.getcwd(), pdfname)
	fld2pdf(image_list, path)
	shutil.rmtree(dir)
	return path 

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
	pdfname = nn[0].strip() + " @Adult_Mangas.pdf" if len(nn) > 1 else nn[0] + ".pdf"
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
	file = await images_to_pdf(doujin.images, pdfname, dir=doujin.code)
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
	os.remove(file)
	here = f"[{mess.chat.title}]({mess.link})."
	await m.edit(f"<b><i>Done Successfully Sent  in {here}</i></b>")

@app.on_message(filters.regex("^[/!]nhentai(?: |$)(.*)"))
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
	pdfname = f"{doujin.code}.pdf"
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
	file = await images_to_pdf(doujin.images, pdfname, dir=doujin.code)
	await bot.send_message(event.chat.id, msg, parse_mode=ParseMode.MARKDOWN)
	await app.send_document(event.chat.id, file)
	await asyncio.gather(m.delete(), bot.send_message(-1001568226560, f"[{title}]({doujin.url})\n\nSuccessfully sent to {event.from_user.mention}"))
	os.remove(file)

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
