import os
from io import BytesIO
from typing import List, BinaryIO
from pathlib import Path
from fpdf import FPDF
from plugins import logger, Config
import re

from PIL import Image, ImageFile

from .img_size import get_image_size

ImageFile.LOAD_TRUNCATED_IMAGES = True

def fld2pdf(files: list,  out: str):
    pdf = Path(f'{out}.pdf')
    try:
        img2pdf(files, pdf)
    except BaseException as e:
        logger.info(f'Image to pdf failed with exception: {e}')
        old_img2pdf(files, pdf)
    return pdf


def new_img(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    return img


def old_img2pdf(files: List[Path], out: Path):
    img_list = [new_img(img) for img in files]
    img_list[0].save(out, resolution=100.0, save_all=True, append_images=img_list[1:])
    for img in img_list:
        img.close()


def pil_image(path: Path) -> (BytesIO, int, int):
    img = new_img(path)
    width, height = img.width, img.height
    try:
        membuf = BytesIO()
        img.save(membuf, format='JPEG')
    finally:
        img.close()
    return membuf, width, height


def img2pdf(files: List[Path], out: Path):
    pdf = FPDF('P', 'pt')
    for imageFile in files:
        img_bytes, width, height = pil_image(imageFile)
        
        pdf.add_page(format=(width, height))

        pdf.image(img_bytes, 0, 0, width, height)

        img_bytes.close()

    #pdf.set_title(out.stem)
    pdf.set_author(Config.PDF_AUTHOR or "t.me/Adult_Mangas")
    pdf.output(out, "F")


def make_thumb(folder, files):
    aspect_ratio = 0.7
    if len(files) > 1:
        with Image.open(files[1]) as img:
            aspect_ratio = img.width / img.height

    thumbnail = Image.open(files[0]).convert('RGB')
    tg_max_size = (300, 300)
    thumbnail = crop_thumb(thumbnail, aspect_ratio)
    thumbnail.thumbnail(tg_max_size)
    thumb_path = folder / 'thumbnail' / f'thumbnail.jpg'
    os.makedirs(thumb_path.parent, exist_ok=True)
    thumbnail.save(thumb_path)
    thumbnail.close()
    return thumb_path


def crop_thumb(thumb: Image.Image, aspect_ratio):
    w, h = thumb.width, thumb.height
    if w * 2 <= h:
        b = int(h - (w / aspect_ratio))
        if b <= 0:
            b = w
        thumb = thumb.crop((0, 0, w, b))
    return thumb
