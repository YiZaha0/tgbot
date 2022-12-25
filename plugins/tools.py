import os, io, glob, string, datetime

from telethon.tl.types import MessageEntityPre
from telethon.utils import add_surrogate
from telethon.sync import events
from telethon.errors.rpcerrorlist import MessageTooLongError
from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from telegraph import upload_file
from telethon.utils import pack_bot_file_id
from .readp import get_names, get_soup, get_link, anext, iter_chapters_ps
from . import *

async def get_amessages():
 mid = get_db("MID")
 try:
  if globals()["messages"][-1].id +1 == mid: 
   return globals()["messages"]
  else:
   raise KeyError
 except:
  global messages
  messages = await bot.get_messages("adult_mangas", ids=list(range(2, int(get_db("MID")))))
  return messages

async def update_plist():
	data = dict()
	mess = await get_amessages()
	for m in mess:
		if m and m.text and "releasing" in m.text.lower() and "+" in m.message:
			name = m.raw_text.split("\n")[0].split(" | ")[0].strip()
			link = m.entities[-1].url
			data[name] = link
	pp = sorted(data)
	add_db("PNAMES", pp)
	add_db("PLIST", data)

async def update_pindex():
    az_dict = {"#": list()}
    [az_dict.update({i: list()}) for i in string.ascii_uppercase]
    
    messages = [m for m in await get_amessages() if m and m.text and m.photo and "Type" in m.text]
    
    messages = {m.message.split("\n")[0].split("|")[0].strip():m for m in messages}
    for name in sorted(messages):
        m = messages[name]
        link = f"https://t.me/c/{m.chat.id}/{m.id}"
        f = name[0].upper()
        if not f.isalpha():
            f = "#"
        if "RELEASING" in m.message:
            tick = "🔷"
        elif "FINISHED" in m.message:
            tick = "🔶"
        data = f"{tick} <a href='{link}'>{name}</a>\n"
        az_dict[f].append(data)

    posts = dict()
    for i in az_dict:
        data = f"<b>⛩️ {i}-{i}-{i} ⛩️</b>\n\n"
        posts[data] = ""
        for p in az_dict[i]:
            posts[data] += p
    post_id = 62
    for p in posts:
        try:
            await bot.edit_message(-1001749847496, post_id, p + posts[p], parse_mode="html")
        except:
            pass
        post_id += 1
    mpost = "<i><b>✘ Index Of Manhwas in @Adult_Mangas ✘</i></b>\n\n<i>🔶 = Finished/Completed\n🔷 = Releasing/OnGoing\n\nLast Updated: {}</i>"
    await bot.edit_message(-1001749847496, 36, mpost.format(datetime.datetime.now().__str__().split(".")[0] + f" ({time.tzname[time.daylight]})"), parse_mode="html")

def hb(size):
    if not size:
        return "0 B"
    for unit in ["", "K", "M", "G", "T"]:
        if size < 1024:
            break
        size /= 1024
    if isinstance(size, int):
        size = f"{size}{unit}B"
    elif isinstance(size, float):
        size = f"{size:.2f}{unit}B"
    return size

@app.on_message(filters.regex("/listp ?(.*)") & filters.user(SUDOS))
async def getplist(bot, event):
	pnames = get_names()
	e = await event.reply("`Processing...`")
	plist = get_db("PLIST")
	input_str = event.matches[0].group(1)
	post = ""
	n = 0
	for i in pnames:
		if input_str in ["-c", "--channel", "-p", "--post"]:
			post += f"➤ [{i}]({plist[i]})\n"
		else:
			n += 1
			post += f"{n-1}.] [{i}]({plist[i]})\n"
	await e.delete()
	await e.reply(post)
	

@app.on_message(filters.regex("noformat ?(.*)") & filters.user(SUDOS))
async def mono_format(bot, event):
 reply = event.reply_to_message
 if not reply:
  await event.reply("`Reply to a Message...`")
 else:
  await event.reply(f"<code>{reply.text and reply.text.markdown or reply.caption and reply.caption.markdown}</code>", parse_mode=ParseMode.HTML)


@app.on_message(filters.user(SUDOS) & filters.regex("^/ls ?(.*)"))
async def listdirectory(client, event):
    files = event.matches[0].group(1).strip()
    if not files:
        files = "*"
    elif files.endswith("/"):
        files += "*"
    elif "*" not in files:
        files += "/*"
    files = glob.glob(files)
    if not files:
        return await event.reply_text("`Directory Empty or Incorrect.`")
    pyfiles = []
    jsons = []
    vdos = []
    audios = []
    pics = []
    others = []
    otherfiles = []
    folders = []
    text = []
    apk = []
    exe = []
    zip_ = []
    book = []
    for file in sorted(files):
        if os.path.isdir(file):
            folders.append("📂 " + str(file))
        elif str(file).endswith(".py"):
            pyfiles.append("🐍 " + str(file))
        elif str(file).endswith(".json"):
            jsons.append("🔮 " + str(file))
        elif str(file).endswith((".mkv", ".mp4", ".avi", ".gif", "webm")):
            vdos.append("🎥 " + str(file))
        elif str(file).endswith((".mp3", ".ogg", ".m4a", ".opus")):
            audios.append("🔊 " + str(file))
        elif str(file).endswith((".jpg", ".jpeg", ".png", ".webp", ".ico")):
            pics.append("🖼 " + str(file))
        elif str(file).endswith((".txt", ".text", ".log")):
            text.append("📄 " + str(file))
        elif str(file).endswith((".apk", ".xapk")):
            apk.append("📲 " + str(file))
        elif str(file).endswith((".exe", ".iso")):
            exe.append("⚙ " + str(file))
        elif str(file).endswith((".zip", ".rar")):
            zip_.append("🗜 " + str(file))
        elif str(file).endswith((".pdf", ".epub")):
            book.append("📗 " + str(file))
        elif "." in str(file)[1:]:
            others.append("🏷 " + str(file))
        else:
            otherfiles.append("📒 " + str(file))
    omk = [
        *sorted(folders),
        *sorted(pyfiles),
        *sorted(jsons),
        *sorted(zip_),
        *sorted(vdos),
        *sorted(pics),
        *sorted(audios),
        *sorted(apk),
        *sorted(exe),
        *sorted(book),
        *sorted(text),
        *sorted(others),
        *sorted(otherfiles),
    ]
    text = ""
    fls, fos = 0, 0
    flc, foc = 0, 0
    for i in omk:
        try:
            emoji = i.split()[0]
            name = i.split(maxsplit=1)[1]
            nam = name.split("/")[-1]
            if os.path.isdir(name):
                size = 0
                for path, dirs, files in os.walk(name):
                    for f in files:
                        fp = os.path.join(path, f)
                        size += os.path.getsize(fp)
                if hb(size):
                    text += emoji + f" `{nam}`" + "  `" + hb(size) + "`\n"
                    fos += size
                else:
                    text += emoji + f" `{nam}`" + "\n"
                foc += 1
            else:
                if hb(int(os.path.getsize(name))):
                    text += (
                        emoji
                        + f" `{nam}`"
                        + "  `"
                        + hb(int(os.path.getsize(name)))
                        + "`\n"
                    )
                    fls += int(os.path.getsize(name))
                else:
                    text += emoji + f" `{nam}`" + "\n"
                flc += 1
        except BaseException:
            pass
    tfos, tfls, ttol = hb(fos), hb(fls), hb(fos + fls)
    if not hb(fos):
        tfos = "0 B"
    if not hb(fls):
        tfls = "0 B"
    if not hb(fos + fls):
        ttol = "0 B"
    text += f"\n\n`Folders` :  `{foc}` :   `{tfos}`\n`Files` :       `{flc}` :   `{tfls}`\n`Total` :       `{flc+foc}` :   `{ttol}`"
    try:
        await client.send_message(event.chat.id, text, reply_to_message_id=event.id)
    except errors.BadRequest:
        with io.BytesIO(str.encode(text)) as out_file:
            out_file.name = "output.txt"
            await client.send_document(event.chat.id, out_file, reply_to_message_id=event.id, caption=f"`{event.text}`")
        await event.delete()


@app.on_message(filters.user(SUDOS+[5591954930]) & filters.regex("^/thumbnail ?(.*)"))
async def setthumb(bot, event):
	reply = event.reply_to_message
	if reply and reply.photo:
		image = await reply.download("./thumb.jpg")
		xx = "https://telegra.ph" + upload_file(image)[0]
		add_db("THUMBNAIL", xx)
		await event.reply("`Custom thumbnail set.`")
	elif reply and reply.document and reply.document.thumbs:
		image = await bot.download_media(reply.document.thumbs[-1].file_id, file_name="./thumb.jpg")
		xx = "https://telegra.ph" + upload_file(image)[0]
		add_db("THUMBNAIL", xx)
		await event.reply("`Custom thumbnail set.`")
	else:
		await event.reply("`Reply to Photo or media with thumb...`")

async def update_thumbnail():
	url = get_db("THUMBNAIL")
	if url:
		await req_download(url.replace("telegra.ph", "graph.org"), filename="thumb.jpg")

@app.on_message(filters.private & filters.forwarded)
async def forwardedChatID(bot, event):
	forward_info = event.forward_from_chat
	if forward_info.type:
		await event.reply_text(f"<strong>Your Chat ID is <code>{forward_info.id}</code></strong>")

@app.on_message(filters.chat(-1001606385356) & filters.caption)
async def _mid(client, event):
	add_db("MID", event.id+1)
	if "RELEASING" in event.caption:
		await update_plist()
	if "Status" in event.caption:
		await update_pindex()

@app.on_message(filters.chat(-1001666665549) & filters.linked_channel & ~filters.sticker)
async def _(bot, update):
	await update.unpin()
	await update.delete()

@app.on_message(filters.command("logs") & filters.user(SUDOS))
async def logs(bot, update):
    response = await update.reply("`Processing...`")
    await response.delete()
    await update.reply_document("LOGS.txt", quote=False)

#SUBS
def get_title(link, ps=None):
	bs = get_soup(link)
	if ps == "Manhwa18":
		return bs.title.string.replace("Read", "").strip().split("Manhwa at")[0].strip()
	
	elif ps == "Toonily":
		return bs.find("div", "post-title").find("h1").text.strip()
	
	elif ps == "Manganato":
		return bs.find(class_="story-info-right").find("h1").text.strip()
	else:
		raise ValueError(f"Invalid Site: {ps}")

def get_ps(link):
	if "toonily.com" in link:
		return "Toonily"
	elif "manhwa18.cc" in link:
		return "Manhwa18"
	elif "chapmanganato.com" in link:
		return "Manganato"
	else:
		raise ValueError("Invalid Ps Link: {link}")

@app.on_message(filters.command("msub") & filters.user(SUDOS+[5591954930]) & filters.private)
async def msub(_, update):
	try:
		cmd, link, chat = update.text.split()
		link = get_link(link)
		ps = get_ps(link)
		chat = int(chat)
		title = get_title(link, ps)
		last_chapter = await anext(iter_chapters_ps(link, ps))
	except:
		return await update.reply("Give a valid url and chat_id.")
	
	data = {"msub": ps, "title": title, "link": link, "chat": chat, "last_chapter": last_chapter}
	_sub = db.find_one(data)
	if _sub:
		db.delete_one(_sub)
	db.insert_one(data)
	await update.reply(f"Successfully added `{link}` [{ps}] to db with chat `{chat}`")

@app.on_message(filters.command("rmsub") & filters.user(SUDOS+[5591954930]) & filters.private)
async def rmsub(_, update):
	try:
		cmd, link = update.text.split()
		ps = get_ps(link)
	except:
		return await update.reply("Give a valid link to remove it from subscription.")
	
	data = db.find_one({"msub": ps, "link": link}) 
	if not data:
		return await update.reply("Link doesn't exist in subscriptions db.")
	
	db.delete_one(data)
	await update.reply(f"Successfully removed `{link}` from db")

@app.on_message(filters.command("subs") & filters.user(SUDOS+[5591954930]) & filters.private)
async def listsubs(_, update):
	subs_dict = dict()
	count = 0
	for sub in db.find({"msub": {"$exists": 1}}):
		ps = sub["msub"]
		if ps not in subs_dict:
			subs_dict[ps] = list()
		ps = subs_dict[ps]
		link = sub["link"]
		title = sub["title"]
		chat = sub["chat"]
		msg = f"{title} [{link}]\n→{chat}\n"
		count += 1
		ps.append(msg)
	
	text = f"Total Manhwa Subs: {count} ↓"
	for ps in subs_dict:
		for msg in subs_dict[ps]:
			if ps not in text:
				text += f"\n\n{ps}:\n"
			text += msg
	
	if not count:
		await update.reply("No subs added!")
	else:
		if len(text) > 4096:
			with io.BytesIO(str.encode(text)) as f:
				f.name = "subs.txt"
				await update.reply_document(f)
		else:
			await update.reply(text)
