from aiogram import Bot
import os

token = os.environ.get('BOT_TOKEN')
botApp = Bot(token=token)


async def send_message(chat_id, message):
    if len(message) > 4095:
        for x in range(0, len(message), 4095):
            await botApp.send_message(message, text=message[x:x+4095])
    else:
        await botApp.send_message(chat_id, message)
