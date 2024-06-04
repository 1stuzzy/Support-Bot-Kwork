from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from sql import Database


storage = MemoryStorage()
bot = Bot('7137639336:AAEsk-u3xtjAb_QYteQB2OutOQaVgQ1llzY', parse_mode='HTML')
db = Database('db.db')
dp = Dispatcher(bot, storage=storage)


