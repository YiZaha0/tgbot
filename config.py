import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(".env")

class Config:
	def __init__(self):
		super().__init__()

	def get(self, value, *args, **kwargs):
		return os.environ.get(value, *args, **kwargs)

	def __getattr__(self, value):
		return self.get(value)

	def __getitem__(self, value):
		return os.environ[value]

	def __repr__(self):
		return str(os.environ)

Config = Config()
