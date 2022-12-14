import time
import math
from .fast_telethon import time_formatter

def humanbytes(size):
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

No_Flood = dict()
async def progress(current, total, message, start, ps_type, file_name=None):
    now = time.time()
    if No_Flood.get(message.chat.id):
        if No_Flood[message.chat.id].get(message.id):
            if (now - No_Flood[message.chat.id][message.id]) < 1.1:
                return
        else:
            No_Flood[message.chat.id].update({message.id: now})
    else:
        No_Flood.update({message.chat.id: {message.id: now}})
    diff = time.time() - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        time_to_completion = round((total - current) / speed) * 1000
        progress_str = "`[{0}{1}] {2}%`\n\n".format(
            "".join("●" for i in range(math.floor(percentage / 5))),
            "".join("" for i in range(20 - math.floor(percentage / 5))),
            round(percentage, 2),
        )

        tmp = (
            progress_str
            + "`{0} of {1}`\n\n`✦ Speed: {2}/s`\n\n`✦ ETA: {3}`\n\n".format(
                humanbytes(current),
                humanbytes(total),
                humanbytes(speed),
                time_formatter(time_to_completion),
            )
        )
        if file_name:
            await message.edit(
                "**✦ Status :** `{}`\n\n`File Name: {}`\n\n{}".format(ps_type, file_name, tmp)
            )
        else:
            await message.edit("**✦ Status :** `{}`\n\n{}".format(ps_type, tmp))
