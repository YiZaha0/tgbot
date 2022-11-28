import re
import os
import html 
import tempfile
import urllib
import time
from bs4 import BeautifulSoup
import shutil
import random
import requests
import cloudscraper
import img2pdf
import glob
import logging
import zipfile
import fitz
from reportlab.pdfgen import canvas
from PIL import Image
from AnilistPython import Anilist
from natsort import natsorted
from pathlib import Path 
from urllib.parse import urljoin
from plugins import *
from .pdf import fld2pdf, img2pdf as makefpdf

session = requests.Session()
session.headers["User-Agent"] = random.choice(agents)
logger = logging.getLogger(__name__)

def get_soup(url, parser="html.parser"):
	scraper = cloudscraper.create_scraper()
	req = scraper.get(url)
	req.raise_for_status()
	return BeautifulSoup(req.text, parser)

def ppost(name):
	ani = Anilist()
	try:
		manga = ani.get_manga(name)
	except BaseException:
		return
	en_name = manga.get("name_english") or "N/A"
	ja_name = manga.get("name_romaji") or "N/A"
	type = manga.get("release_format")
	ar = manga.get("average_score") or "N/A"
	status = manga.get("release_status")
	chno = manga.get("chapters") or "N/A"
	genres = ", ".join(natsorted(manga.get("genres")))
	post = f"<b>{en_name} | {ja_name}</b>\n\n➤ <b>Type :</b> {type}\n➤ <b>Average Rating :</b> {ar}\n➤ <b>Status :</b> {status}\n➤ <b>No of Chapters :</b> {chno}\n➤ <b>Genres :</b> {genres}"
	return post

def get_names():
	return get_db("PNAMES")

def clean(name, length=-1):
    while '  ' in name:
        name = name.replace('  ', ' ')
    name = name.replace(':', '')
    if length != -1:
        name = name[:length]
    return name

def convert_pdf(path, images: list):
	doc = fitz.open()
	for i, f in enumerate(images):
		img = fitz.open(f)
		rect = img[0].rect
		pdfbytes = img.convert_to_pdf()
		img.close()
		imgPdf = fitz.open("pdf", pdfbytes)
		page = doc.new_page(width=rect.width, height=rect.height)
		page.show_pdf_page(rect, imgPdf, 0)
	doc.save(path)
	return 
	
def create_pdf(path, images: list):
	pdf = canvas.Canvas(path)

	for image in images:

		# noinspection PyBroadException
		try:
			with Image.open(image) as img:
				w, h = img.size

		except BaseException:
			continue

		pdf.setPageSize((w, h))  # Set the page dimensions to the image dimensions

		pdf.drawImage(image, x=0, y=0)  # Insert the image onto the current page

		pdf.showPage()  # Create a new page ready for the next image

	pdf.save()
	return path


def merge_pdfs(pdflist: list, pdfname):
	result = fitz.open()
	for pdf in pdflist:
		with fitz.open(pdf) as file:
			result.insert_pdf(file)
	result.save(pdfname)
	return pdfname

def images_to_pdf(path: Path, images):
	if not isinstance(path, Path):
		path = Path(path)
	full_path = path.absolute().as_posix()
	with path.open("wb") as pdf:
		try:
			pdf.write(img2pdf.convert(images, producer="t.me/Adult_Mangas", creator="t.me/Adult_Mangas", title=path.stem))
		except:
			create_pdf(full_path, images)
	
	return full_path

async def post_ws(link, pdfname, class_="wp-manga-chapter-img", src="src", fpdf=False):
	req = await req_url(link, headers=session.headers)
	if not str(req.status).startswith("2"):
		req = cloudscraper.create_scraper().get(link)
	rurl = str(req.url)
		
	if ("manhwa18" in rurl or "manhwahentai" in rurl or "toonily" in rurl) and "chapter" not in rurl:
		return pdfname 
	
	content = await req_content(rurl) if hasattr(req, "read") else req.content
	soup = BeautifulSoup(content, "html.parser")
	items = soup.find_all("img", class_)
	if not items:
		return pdfname

	ch = re.findall("\d*\.*\d+", pdfname) or ["chapter"]
	ch = ch[0].strip()
	dir_name = f"manga_{ch}"
	os.path.exists(dir_name) or os.mkdir(dir_name)
	headers = dict()
	headers["Referer"] = rurl
	images = list()
	Process = list()
	
	n = 0
	for item in items:
		url = item.get(src) or item.get("data-src")
		if not url:
			continue
		url = url.strip()
		image_path = os.path.join(dir_name, f"{n}.jpg")
		Process.append(req_download(url, filename=image_path, headers=headers))
		images.append(image_path)
		n += 1
	
	await asyncio.gather(*Process)
	
	path = Path(pdfname)
	
	if fpdf:
		fld2pdf(images, path.stem)
	else:
		images_to_pdf(path, images)
				
	shutil.rmtree(dir_name)
	return path


async def dl_chapter(url, title, mode):
	dir = tempfile.mkdtemp()

	soup = get_soup(url)
	images_list = soup.find("div", "container-chapter-reader").find_all("img")
	n = 0
	process = list()
	images = list()
	for link in images_list:
		link = link.get("src") or link.get("data-src") # for manganelo
		filename = f"{dir}/{n}.jpg"
		headers = dict(Referer=url)
		process.append(req_download(link, filename=filename, headers=headers))
		images.append(filename)
		n += 1
	await asyncio.gather(*process)
	if mode == "pdf":
		file = os.path.join(os.getcwd(), title)
		pdf = fld2pdf(images, file)
		shutil.rmtree(dir)
		return pdf
	if mode == "cbz":
		file = os.path.join(os.getcwd(), title+".cbz")
		with zipfile.ZipFile(file, "w") as cbz:
			for image in images:
				cbz.write(image, compress_type=zipfile.ZIP_DEFLATED)
			return file
	
class nhentai:
	def __init__(self, link):
		if not link.isdigit():
			link = link
			code_regex = re.findall("\d*\.*\d+", link)
			self.code = code_regex[0] if code_regex else "N/A"
		else:
			self.code = link
			link = f"https://nhentai.to/g/{link}/"
		response = requests.get(link)
		response.raise_for_status()
		soup = BeautifulSoup(response.text, "html.parser")
		self.title = soup.find("div", id="info").find("h1").text
		self.tags = []
		self.artists = []
		self.parodies = []
		self.categories = []
		self.languages = []
		self.images = []
		self.read_url = response.url + "1" if response.url.endswith("/") else response.url + "/1"
		self.url = response.url
		tdata = soup.find_all("a", "tag")
		for t in tdata:
			if "tag" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.tags.append("#"+t.text.strip().replace(" ", "_").replace("-", "_"))
			elif "artist" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.artists.append(t.text.strip().replace(" ", "_"))
			elif "parody" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.parodies.append(t.text.strip().replace(" ", "_"))
			elif "language" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.languages.append(t.text.strip().replace(" " , "_"))
			elif "category" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.categories.append("#"+t.text.strip().replace(" ", "_"))
		data = soup.find_all("img", "lazyload")

		for i in data:
			i = i["data-src"].split("\t")[-1].replace("t.", ".")
			if i.endswith("/"):
				continue 
			self.images.append(i)
		self.pages = len(self.images)

class Minfo:
	def __init__(self, id, nelo=False):
		baseurl = "https://ww5.manganelo.tv/manga/" if nelo else "https://readmanganato.com/"
		url = baseurl + id
		soup = get_soup(url)
		self.url = url
		self.id = id
		self.title: str = soup.find(class_="story-info-right").find("h1").text.strip()
		self.alternatives: str = self._fetch_alternatives(soup) or "N/A"
		self.status: str = soup.find("i", "info-status").findNext("td", class_="table-value").text.strip()
		self.poster_url: str = soup.find("div", class_="story-info-left").find("img", class_="img-loading").get("src") if not nelo else "https://ww5.manganelo.tv{}".format(soup.find("div", class_="story-info-left").find("img", class_="img-loading").get("src"))
		self.description: str = html.unescape(soup.find("div", class_="panel-story-info-description").text).strip()
		self.genres: list[str] = [x.text.strip() for x in soup.find("i", class_="info-genres").findNext("td", class_="table-value").find_all("a", "a-h")]
		self.views: str = soup.find("div", class_="story-info-right-extent").find_all("span", class_="stre-value")
		self.views: str = self.views[1].text.strip() if len(self.views) > 1 else None
		self.authors: list[str] = [x.strip() for x in soup.find("i", class_="info-author").findNext("td", class_="table-value").text.split(" - ")]
		self.updated: str = soup.find("div", class_="story-info-right-extent").find_all("span", class_="stre-value")[0].text.strip()
		self.chapters: dict = self._parse_chapters(soup)
		
	def _parse_chapters(self, soup):
		data = dict()
		panels = [x.find("a") for x in soup.find(class_="panel-story-chapter-list").find_all(class_="a-h")]
		for c in panels[::-1]:
			chapter = c["href"].split("-")[-1].strip()
			link = c["href"]
			if not link.startswith("http"):
				link = "https://ww5.manganelo.tv" + link
			data[chapter] = link
		return data

	def _fetch_alternatives(self, soup):
		data = soup.find(class_="story-info-right").find("h2")
		if data:
			return data.text.strip()

def fetch_headers(url, rurl):
	return {
            'Accept': 'image/png,image/svg+xml,image/*;q=0.8,video/*;q=0.8,*/*;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/13.1.2 Safari/605.1.15',
            'Host': urllib.parse.urlparse(url).netloc, 'Accept-Language': 'en-ca', 'Referer': rurl,
            'Connection': 'keep-alive'
        }

async def updates_from_ps(ps=None):
	if ps == "Manhwa18":
		base = "https://manhwa18.cc/"
		content = await req_content(base, headers=session.headers)
		soup = BeautifulSoup(content, "html.parser")
		items = soup.find("div", "manga-lists")
		data = dict()
		for item in items.find_all("div", "data wleft"):
			manga_url = urljoin(base, item.find("a")["href"])
			chapter_url = urljoin(base, item.findNext("div", "chapter-item wleft").find("a")["href"])
			data[manga_url] = chapter_url
	
	elif ps == "Toonily":
		base = "https://toonily.com/"
		content = await req_content(base, cookies={"toonily-mature": "1"})
		soup = BeautifulSoup(content, "html.parser")
		items = soup.find_all("div", "page-item-detail manga")
		data = dict()
		for item in items:
			manga_url = item.find("a")["href"]
			chapter_url = item.find("div", "chapter-item").find("a")["href"]
			data[manga_url] = chapter_url
	
	else:
		raise ValueError
	
	return data
          
