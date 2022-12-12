from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus, MessageEntityType

from . import *

rchats = dict()
rchats[-1001568226560] = -1001459727128 # requestGroup = requestChannel

rgroups = list(rchats.keys()) # requestGroups
rchannels = list(rchats.values()) # requestChannels

def get_request_from_text(text):
	requestRegex = "[#!/][rR][eE][qQ][uU][eE][sS][tT] "
	requestMatch = re.match(requestRegex, text)
	if requestMatch:
		text = text.replace(requestMatch.group(), "").strip()
	return text 

@app.on_message(filters.command("request", prefixes=["/", "!", "#"]) & filters.chat(rgroups))
async def _requests(client, update):
	reply = update.reply_to_message
	if reply:
		text = get_request_from_text(reply.text)
		user_mention = reply.from_user.mention
	else:
		_, text = update.text.split(" ")
		user_mention = update.from_user.mention 
		
	chat_tosend = rchats[update.chat.id]
	text_tosend = f"Request By {user_mention}\n\n<code>{text}</code>"
	buttons_tosend = list()
	buttons_tosend.append([InlineKeyboardButton("Request Message", url=update.link)])
	buttons_tosend.append([InlineKeyboardButton("Done", r"rcompleted"), InlineKeyboardButton("Reject", r"rrejected")])
	buttons_tosend.append([InlineKeyboardButton("Unavailable", "runavailable"), InlineKeyboardButton("Already Available", "ralready_available")])
	
	await app.send_message(
		chat_tosend,
		text_tosend,
		reply_markup=InlineKeyboardMarkup(
			buttons_tosend
			)
		)
	
	await app.send_message(
		update.chat.id,
		f"Hi {user_mention}, your request for <code>{text}</code> has been submitted to the admins.\n\n<b>Please Note that Admins might be busy. So, this may take more time.</b>",
		reply_to_message_id=update.reply_to_message_id or update.id
		)

@app.on_callback_query(filters.chat(rchannels))
async def cb_requests(client, update):
	message = update.message
	sender = await app.get_chat_member(message.chat.id, update.from_user.id)
	if not sender or sender.status.type != ChatMemberStatus.ADMINISTRATOR:
		await update.answer(
			"Not your place to click, {update.from_user.first_name}"
		)
	action = update.data.replace("r", "", 1).replace("_", " ")
	user_id = 123456789
	user_name = message.text.split("\n")[0].replace("Request By", "").strip()
	for e in message.entities:
		if e.type == MessageEntityType.TEXT_MENTION:
			user_id = e.user.id
			break 
	user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
	tosend = f"Hey {user_mention}, your request"
	toedit = f"<b>﹀{action.title()}﹀<b>\n\n<s>{message.text.html}</s>"
	
	try:
		await app.send_message(
			user_id,
			tosend
		)
	except:
		pass 
	
	await message.edit_text(
		toedit,
		reply_markup=None
	)
	
