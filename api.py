import logging
from aiohttp import web
from config import Config

logging.basicConfig(level=logging.INFO)

async def root(request):
    return web.Response(text="Online!")

app = web.Application()
app.add_routes([web.get("/"), root])

if __name__ == "__main__:
    web.run_app(app, port=Config.PORT)
