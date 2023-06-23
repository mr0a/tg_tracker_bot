from aiogram import Bot
import os

token = os.environ.get('BOT_TOKEN')
botApp = Bot(token=token)


async def send_message(chat_id, text):
    await botApp.send_message(chat_id, text)
