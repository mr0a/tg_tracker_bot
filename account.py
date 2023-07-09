import os
from telethon import TelegramClient

user_client: TelegramClient = None  # type: ignore

api_hash = os.environ.get('API_HASH')
api_id = os.environ.get('API_ID')

if not api_hash or not api_id:
    raise Exception('API_HASH or API_ID has not been set!')


async def getUserClient():
    global user_client
    if not user_client:
        user_client = TelegramClient(
            'anon_main', api_hash=api_hash, api_id=int(api_id))
        await user_client.connect()
    return user_client
