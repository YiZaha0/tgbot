from pathlib import Path 
from datetime import datetime

from pyrogram import filters

from . import *

TMP_DL_DIR = Config.TMP_DL_DIR or "downloads"

@app.on_message(filters.regex(r"^/(download|dl) ?(.*)", re.IGNORECASE) & filters.user(SUDOS))
async def dl_download(client, update):
	input_str = update.matches[0].group(2)
	reply = update.reply_to_message
	msg = await update.reply(
		"<code>Processing...</code>"
	)
	
	if reply and reply.media:
		start_time = datetime.now()
		file_path = TMP_DL_DIR + "/"
		if input_str.strip():
			if "/" in input_str:
				file_path = input_str.strip()
			else:
				file_path = os.path.join(TMP_DL_DIR, input_str.strip())
		path = Path(file_path)
		path.parent.mkdir(parents=True, exist_ok=True)
		c_time = time.time()
		downloaded_path = await reply.download(
			file_name=file_path,
			progress=progress,
			progress_args=(msg, c_time, "Downloading...")
		)
		end_time = datetime.now()
		time_taken = (end_time - start_time).seconds 
		await msg.edit(
			f"Successfully downloaded to <code>{downloaded_path}</code> in <code>{time_taken}</code> seconds."
		)
		
	elif input_str:
		start_time = datetime.now()
		dl_url = input_str
		file_path = os.path.basename(dl_url)
		if "|" in input_str:
			splited_input = input_str.split("|")
			dl_url = splited_input[0].strip()
			file_path = splited_input[1].strip()
		if not "/" in file_path:
			file_path = os.path.join(TMP_DL_DIR, file_path)
		c_time = time.time()
		try:
			downloaded_path, _ = await fast_download(
				dl_url,
				file_path,
				progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
					progress(
						d,
						t,
						msg,
						c_time,
						f"Downloading URL - {dl_url}"
					)
				)
			)
		except Exception as e:
			return await msg.edit(
				f"<b>Something Went Wrong❗</b>\n\n<code>{e.__class__.__name__}: {e}"
			)
	else:
		return await msg.edit(
			f"<code>Repy to a media or give a url to download."
		)

@app.on_message(filters.regex(r"^/(ul|up|upload) ?(.*)", re.IGNORECASE) & filter.user(SUDOS))
async def up_upload(client, update):
	input_str = update.matches[0].group(2)
	msg = await update.reply(
		"<code>Processing...</code>"
	)
	chat = update.chat.id
	thumb = "thumb.jpg" if "-t" in input_str.strip() else None
	force_doc = False if "-s" in input_str.strip() else True 
	
	flags = ("-t", "-s")
	for _f in flags:
		input_str = input_str.replace(_f, "").strip()
	
	if "|" in input_str:
		splited_input = input_str.split("|")
		input_str = splited_input[0].strip()
		chat = splited_input[1].strip()
	
	try:
		chat = int(chat)
	except:
		return await msg.edit(
			"<code>Invalid chat id given</code>"
		)
		
	if input_str.endswith("/"):
		input_str += "*"
	files = glob.glob(input_str) 
	
	if not files and os.path.exists(input_str):
		files = [input_str]
	
	if not files and not os.path.exists(input_str):
		return await msg.edit(
			"<code>Give the filename to upload.</code>"
		)
	start_time = datetime.now()
	for file in files:
		if os.path.exists(file):
			continue 
		try:
			c_time = time.time()
			await app.send_document(
				chat,
				file,
				force_document=force_doc,
				thumb=thumb,
				progress=progress,
				progress_args=(msg, c_time, "Uploading...", file)
			)
		except Exception as e:
			return await msg.edit(
				f"<b>Something Went Wrong❗</b>\n\n<code>{e.__class__.__name__}: {e}"
			)
	end_time = datetime.now()
	time_taken = (end_time - start_time).seconds 
	if chat != update.chat.id:
		await msg.edit(
			f"Successfully upload <code>{input_str}</code> to <code>{chat}</code> in <code>{time_taken}</code> seconds."
		)
	else:
		await msg.edit(
			f"Successfully upload <code>{input_str}</code> in <code>{time_taken}</code> seconds." 
		)
		
