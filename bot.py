from aiogram import Bot
import os

token = os.environ.get('BOT_TOKEN')
if not token:
    raise Exception("Bot token is not set!")
botApp = Bot(token=token)


def getBotClient():
    return botApp
