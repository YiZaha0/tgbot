import re
import os
import time
import glob 
import html
import json
import urllib
import shutil
import random
import requests
import tempfile
import zipfile
import cloudscraper
import img2pdf
import fitz

from pathlib import Path
from urllib.parse import urljoin
from natsort import natsorted
from reportlab.pdfgen import canvas
from AnilistPython import Anilist
from bs4 import BeautifulSoup

from .pdf import Image, fld2pdf
from .. import *

# –––·Required Vars·–––
session = requests.Session()
session.headers["User-Agent"] = random.choice(agents)


# –––·Utilities·–––
def get_soup(url, parser="html.parser"):
	scraper = cloudscraper.create_scraper()
	req = scraper.get(url)
	req.raise_for_status()
	return BeautifulSoup(req.text, parser)

def get_names():
	return get_db("PNAMES")

def clean(name, length=-1):
    while '  ' in name:
        name = name.replace('  ', ' ')
    name = name.replace(':', '')
    if length != -1:
        name = name[:length]
    return name

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
	post = f"<b>{en_name} | {ja_name}</b>\n\n━━━━━━━━━━━━━━━━━━━━━━\n➤ <b>Type :</b> {type}\n➤ <b>Average Rating :</b> {ar}\n➤ <b>Status :</b> {status}\n➤ <b>No. of Chapters :</b> {chno}\n➤ <b>Genres :</b> {genres}\n━━━━━━━━━━━━━━━━━━━━━━"
	return post

def img_headers(url, referer):
	return {
            'Accept': 'image/png,image/svg+xml,image/*;q=0.8,video/*;q=0.8,*/*;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': random.choice(agents),
            'Host': urllib.parse.urlparse(url).netloc, 'Accept-Language': 'en-ca', 'Referer': referer,
            'Connection': 'keep-alive'
        }


# –––·PDF Utilities·–––
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

		try:
			with Image.open(image) as img:
				w, h = img.size

		except BaseException:
			continue

		pdf.setPageSize((w, h))  

		pdf.drawImage(image, x=0, y=0)  

		pdf.showPage()  

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
	

# –––·P-Downloader Utilities·–––
async def post_ws(link, pdfname, class_="wp-manga-chapter-img", src="src", fpdf=False):
	req = requests.get(link, headers=session.headers)
	if req.status_code != 200:
		req = cloudscraper.create_scraper().get(link)

	rurl = req.url
		
	if ("manhwa18" in rurl or "manhwahentai" in rurl or "toonily" in rurl) and "chapter" not in rurl:
		return pdfname 
	
	content = req.content

	soup = BeautifulSoup(content, "html.parser")
	items = soup.find_all("img", class_)
	if not items:
		return pdfname

	ch = re.findall("\d*\.*\d+", pdfname) or ["chapter"]
	ch = ch[0].strip()
	dir_name = f"manga_{ch}"
	os.path.exists(dir_name) or os.mkdir(dir_name)
	headers = dict(session.headers)
	headers["Referer"] = rurl
	images = list()
	Process = list()
	
	n = 0
	for item in items:
		url = item.get(src) or item.get("data-src")
		if not url:
			continue
		url = url.strip()
		ext = url.split("/")[-1].split(".")[1]
		image_path = os.path.join(dir_name, f"{n}.{ext}")
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


# –––·Nhentai Scraper·–––
class Nhentai:
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
				self.tags.append("#"+t.text.strip().split("\n")[0].replace(" ", "_").replace("-", "_"))
			elif "artist" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.artists.append("#"+t.text.strip().split("\n")[0].replace(" ", "_"))
			elif "parody" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.parodies.append("#"+t.text.strip().split("\n")[0].replace(" ", "_"))
			elif "language" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.languages.append("#"+t.text.strip().split("\n")[0].replace(" " , "_"))
			elif "category" in t["href"]:
				t = t.find(class_="name") if "xxx" in self.url else t
				self.categories.append("#"+t.text.strip().split("\n")[0].replace(" ", "_"))
		data = soup.find_all("img", "lazyload")

		for i in data:
			i = i["data-src"].split("\t")[-1].replace("t.", ".")
			if i.endswith("/"):
				continue 
			self.images.append(i)
		self.pages = len(self.images)
		
		
# –––·Manga Utilities ·–––
class Minfo: 
	def __init__(self, id, nelo=False):
		baseurl = "https://ww5.manganelo.tv/manga/" if nelo else "https://readmanganato.com/"
		url = session.get(baseurl + id).url
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
			
async def dl_chapter(url, title, mode): 
	dir = tempfile.mkdtemp()
	content = await req_content(url, headers=session.headers)
	soup = BeautifulSoup(content, "html.parser")
	if "manganato" in url or "manganelo" in url:
		images_list = soup.find("div", "container-chapter-reader").find_all("img")
		images_list = [(i.get("src") or i.get("data-src")).strip() for i in images_list]
	elif "mangabuddy" in url:
		img_base = "https://s1.mbcdnv1.xyz/file/img-mbuddy/manga/"
		regex = r"var chapImages = '(.*)'" 
		images_list = re.findall(regex, soup.prettify())[0].split(",")
		images_list = [img_base + i.strip() for i in images_list]
	else:
		raise ValueError("Invalid Url : {!r}".format(url))
	n = 0
	process = list()
	images = list()
	headers = dict(session.headers)
	headers["Referer"] = url
	for link in images_list:
		filename = f"{dir}/{n}.{link.split('/')[-1].split('.')[-1] or 'jpg'}"
		await req_download(link, filename=filename, headers=headers)
		images.append(filename)
		n += 1

	if mode == "pdf":
		file = os.path.join(os.getcwd(), title)
		try:
			pdf = fld2pdf(images, file)
		except:
			pdf = images_to_pdf(file+".pdf", images)
		shutil.rmtree(dir)
		return pdf
	if mode == "cbz":
		file = os.path.join(os.getcwd(), title+".cbz")
		with zipfile.ZipFile(file, "w") as cbz:
			for image in images:
				cbz.write(image, compress_type=zipfile.ZIP_DEFLATED)
		shutil.rmtree(dir)
		return file


# –––·AutoManga Utilities·–––
async def iter_chapters_ps(link, ps=None):
	if ps == "Manhwa18":
		bs = get_soup(link)
		urls = list()
		for item in bs.find("div", "panel-manga-chapter wleft").find_all("a"):
			yield urljoin("https://manhwa18.cc/", item["href"])
	
	elif ps == "Toonily":
		bs = get_soup(link)
		urls = dict()
		for item in bs.find_all("li", "wp-manga-chapter"):
			yield item.find("a")["href"]
	
	elif ps == "Manganato":
		manga_id = link.split("/")[-1]
		manga = Minfo(manga_id)
		for ch_url in reversed(manga.chapters.values()):
			yield ch_url

	elif ps == "Mangabuddy":
		base = "https://mangabuddy.com/"
		splited = link.split("/")
		manga_id = splited[-1] or splited[-2]
		link = f"{base}api/manga/{manga_id}/chapters?source=detail"
		bs = get_soup(link)
		for item in bs.find("ul", id="chapter-list").findAll("li"):
			yield urljoin(base, item.find("a")["href"])

	else:
		raise ValueError("Invalid Site: {!r}".format(ps))

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
		content = await req_content(base, cookies={"toonily-mature": "1"}, headers=session.headers)
		soup = BeautifulSoup(content, "html.parser")
		items = soup.find_all("div", "page-item-detail manga")
		data = dict()
		for item in items:
			manga_url = item.find("a")["href"]
			chapter_url = item.find("div", "chapter-item").find("a")["href"]
			data[manga_url] = chapter_url
	
	elif ps == "Manganato":
		base = "https://manganato.com/"
		content = await req_content(base, headers=session.headers)
		soup = BeautifulSoup(content, "html.parser")
		items = soup.find_all("div", "content-homepage-item")
		data = dict()
		for item in items:
			manga_url = item.findNext("a")["href"]
			chapter_item = item.findNext("p", "a-h item-chapter")
			if not chapter_item:
				continue
			chapter_url = chapter_item.findNext("a")["href"]
			data[manga_url] = chapter_url
	
	elif ps == "Mangabuddy":
		base = "https://mangabuddy.com/"
		home = "https://mangabuddy.com/home-page"
		content = await req_content(home, headers=session.headers)
		soup = BeautifulSoup(content, "html.parser")
		items = soup.find_all("div", "book-item latest-item")
		data = dict()
		for item in items:
			manga_url = urljoin(base, item.a["href"])
			chapter_item = item.findNext("div", "chap-item")
			if not (chapter_item or chapter_item.a):
				continue
			chapter_url = urljoin(base, chapter_item.a["href"])
			if manga_url not in data:
				data[manga_url] = chapter_url
				
	else:
		raise ValueError("Inavlid Site: {!r}".format(ps))
	
	return data

          



