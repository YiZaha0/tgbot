from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup 
from pyrogram.errors import UserIsBlocked, PeerIdInvalid

from . import *

Start_Text = """
Hello {}. I am a Bot working for Pornhwa Hub.
You can contact my owner through me.

━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>• Uptime :</b> <code>{}</code>
<b>• Ping :</b> <code>{} ms</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

@app.on_message(filters.private & filters.command("start"))
async def pm_start(client, update):
	uptime = readable_time(time.time() - bot_start_time)
	s_time = time.time()
	m = await update.reply_text("<code>...</code>")
	t_taken = (time.time() - s_time) * 1000
	ping = f"{t_taken:.3f}"

	await m.edit_text(
		Start_Text.format(
			update.from_user.mention,
			uptime,
			ping 
		),
		reply_markup=InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton(
						"My Channel",
						url="https://t.me/Adult_Mangas"
					),
					InlineKeyboardButton(
						"My Owner",
						user_id=5304356242
					)
				]
			]
		)
	)


@app.on_message(filters.private & filters.incoming & ~filters.user(SUDOS), group=2)
async def pm(_, update):
	await app.resolve_peer(update.from_user.id)
	user_id = update.from_user.id
	user_title = update.from_user.first_name + (update.from_user.last_name or "")
	username = update.from_user.username
	user_data = {"udb": True, "user_id": update.from_user.id, "title": user_title, "username": username}
	user = db.find_one(user_data)
	if not user:
		db.insert_one(user_name)
		await app.send_message(
			LOG_CHAT, 
			"<b>Someone Started Me❗</b>\n\n"
			f"<b>›› Name →</b> <code>{user_title}</code>\n<b>›› Username →</b> <code>{'@'+username or 'N/A'}</code>\n<b>›› Profile Link →</b> [{user_title}](tg://user?id={user_id})")
	await update.forward(OWNER)

@app.on_message(filters.reply & filters.user(OWNER))
async def reply_to_pms(client, update):
	reply = update.reply_to_message
	from_peer = None 
	if update.forward_from:
		from_peer = update.forward_from.username or update.forward_from.id
	else:
		for user in db.find({"udb": {"$exists": 1}}):
			if not user.get("udb"):
				continue
			if update.forward_sender_name == user.get("title"):
				from_peer = user.get("username") or user.get("uid")
	
	if not from_peer:
		logger.error("Couldn't find user's data in pm sadly, not sending message to anyone.") 
		return update.continue_propagation()
	
	try:
		user = await app.get_users(from_peer)
	except PeerIdInvalid:
		logger.info("Couldn't find user's data due to PeerIdInvalide error, not sending message to anyone.")  
		return update.continue_propagation()
		
	try:
		await update.copy(from_peer, caption=update.caption.html if update.caption else None)
	except UserIsBlocked:
		await app.send_message(
			LOG_CHAT,
			f"User [user.first_name](tg://user?id={user.id}) has Blocked Me ❗")
	except Exception as e:
		logger.info(f"Got Error While Sending Message to User [user.first_name](tg://user?id={user.id}): {e}")
		
	update.continue_propagation()
		
