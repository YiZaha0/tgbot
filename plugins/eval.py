from telethon import events, errors, functions, types
import inspect
import traceback
import asyncio
import sys
import io
from . import *
def _parse_eval(value=None):
    if not value:
        return value
    if hasattr(value, "stringify"):
        try:
            return value.stringify()
        except TypeError:
            pass
    elif isinstance(value, dict):
        try:
            return json_parser(value, indent=1)
        except BaseException:
            pass
    return str(value)

def _stringify(text=None, *args, **kwargs):
    if text:
        text = _parse_eval(text)
    return print(text, *args, **kwargs)

@bot.on(admin_cmd(pattern="exec ?(.*)", allow_sudo=True))
async def _(event):
    try:
        cmd = event.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await eod(event, "`Give Something To Execute...`")
    xx = await eor(event, "`Processing...`")
    reply_to_id = event.reply_to_msg_id or event.id
    stdout, stderr = await bash(cmd, run_code=1)
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
            out_file.name = "bash.txt"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                thumb=None,
                allow_cache=False,
                caption=f"`{cmd}`" if len(cmd) < 998 else None,
                reply_to=reply_to_id,
            )

            await xx.delete()
    else:
        await eor(xx, OUT, link_preview=False)

@bot.on(admin_cmd("eval ?(.*)", allow_sudo=True))
async def _(event):
    if event.fwd_from:
        return
    if not event.pattern_match.group(1):
        return await eod(event, "`Give something to execute...`")
    e = await eor(event, "`Processing ...`")
    cmd = event.text.split(" ", maxsplit=1)[1]
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id

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
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=f"```{cmd}```" if len(cmd) < 998 else None,
                reply_to=reply_to_id
            )
            await e.delete()
    else:
        await eor(e, final_output)
async def aexec(code, event):
    exec(
        (
            "async def __aexec(e, client): "
            + "\n print = p = _stringify"
            + "\n message = event = e"
            + "\n reply = await event.get_reply_message()"
            + "\n chat = event.chat_id"
        )
        + "".join(f"\n {l}" for l in code.split("\n"))
    )

    return await locals()["__aexec"](event, event.client)
