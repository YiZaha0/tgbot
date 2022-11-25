#test

from pyrogram import filters
from telethon import errors

from . import *

@app.on_message(filters.private & filters.command("start") & ~filters.user(SUDOS))
async def start(bot, update):
	await update.delete()

@app.on_message(filters.private & filters.incoming & ~filters.user(SUDOS), group=2)
async def pm(_, update):
	await app.resolve_peer(update.from_user.id)
	await bot.get_entity(update.from_user.id)
	user = db.find_one({"uid": update.from_user.id})
	if not user:
		db.insert_one({"uid": update.from_user.id})
		await app.send_message(LOG_CHAT, f"<b>❗New User</b> - {update.from_user.mention}.")
	await update.forward(5304356242)

@bot.on(events.NewMessage(incoming=True, from_users=5304356242, func=lambda e: e.is_private))
async def pm_(event):
	reply = await event.get_reply_message()
	if not reply or not reply.fwd_from or reply.fwd_from.channel_post:
		return 
	from_id = reply.fwd_from.from_id.user_id if reply.fwd_from.from_id else None
	from_name = reply.fwd_from.from_name
	user_mention = f"[{from_name}](tg://user?id={from_id})" if from_id else from_name
	try:
		await bot.send_message(from_id or from_name, event.message)
	except errors.UserIsBlockedError:
		await bot.send_message(LOG_CHAT, f"**❗User** - {user_mention} **has blocked me.**")
		db.delete_one({"uid": update.from_user.id})
	except Exception as e:
		await bot.send_message(LOG_CHAT, f"**❗ Something Went Wrong While Sending Message To** {user_mention}\n\n`{e}`")
		
	
		
