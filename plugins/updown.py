import glob

from pathlib import Path 
from datetime import datetime

from pyrogram import filtersfilters

from .utils.gtools import gen_video_ss, get_video_duration
from . import *


TMP_DL_DIR = Config.TMP_DL_DIR or "downloads"

@app.on_message(filters.regex(r"^/(download|dl) ?(.*)", re.IGNORECASE) & filters.user(SUDOS))
async def dl_download(client, update):
	input_str = update.matches[0].group(2)
	reply = update.reply_to_message
	msg = await update.reply(
		"<code>Processing...</code>"
	)
	if not os.path.isdir(TMP_DL_DIR):
		os.mkdir(TMP_DL_DIR)
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
			downloaded_path, _ = await req_download(
				dl_url,
				file_path,
				progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
					progress(
						d,
						t,
						msg,
						c_time,
						f"Downloading URL - {dl_url}",
						file_path
					)
				)
			)
		except Exception as e:
			return await msg.edit(
				f"<b>Something Went Wrong❗</b>\n\n<code>{e.__class__.__name__}: {e}</code>"
			)
		end_time = datetime.now()
		time_taken = (end_time - start_time).seconds
		await msg.edit(
			f"Successfully downloaded url <code>{dl_url}</code> to <code>{file_path}</code> in <code>{time_taken}</code> seconds."
		)
	else:
		return await msg.edit(
			f"<code>Repy to a media or give a url to download.</code>"
		)

@app.on_message(filters.regex(r"^/(upload|up|ul) ?(.*)", re.IGNORECASE) & filters.user(SUDOS))
async def up_upload(client, update):
	input_str = update.matches[0].group(2)
	msg = await update.reply(
		"<code>Processing...</code>"
	)
	if not input_str:
		return await msg.edit(
			f"<code>Give a file name to upload.</code>"
		)

	chat = update.chat.id
	thumb = "thumb.jpg" if "-t" in input_str.strip() else None
	stream = True if "-s" in input_str.strip() else False
	asdoc = True if "-f" in input_str.strip() else False
	
	flags = ("-t", "-s", "-f")
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
			"<code>File doesn't exist.</code>"
		)
	start_time = datetime.now()
	for file in files:
		if os.path.isdir(file):
			continue 
		try:
			c_time = time.time()
			if stream:
			    ss, duration = get_ss_and_duration(file)
			    if not thumb:
				thumb = ss
			    await app.send_video(
			        chat,
			        file,
			        thumb=thumb,
			        duration=duration,
			        progress=progress,
			        progress_args=(msg, c_time, "Uploading...", file)
				)
			    if ss:
			        os.remove(ss)
			else:
			    await app.send_document(
			        chat,
			        file,
			        force_document=asdoc,
			        thumb=thumb,
			        progress=progress,
			        progress_args=(msg, c_time, "Uploading...", file)
				)
		except Exception as e:
			return await msg.edit(
				f"<b>Something Went Wrong❗</b>\n\n<code>{e.__class__.__name__}: {e}</code>"
			)
	end_time = datetime.now()
	time_taken = (end_time - start_time).seconds 
	if chat != update.chat.id:
		await msg.edit(
			f"Successfully uploaded <code>{input_str}</code> to <code>{chat}</code> in <code>{time_taken}</code> seconds."
		)
	else:
		await msg.edit(
			f"Successfully uploaded <code>{input_str}</code> in <code>{time_taken}</code> seconds." 
		)
		
async def get_ss_and_duration(video_path: str):
	thumb, duration = None, None 
	try:
		thumb = gen_video_ss(video_path)
	except:
		pass 
	try:
		duration = get_video_duration(video_path)
	except:
		pass 
	return thumb, duration
