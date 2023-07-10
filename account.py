import os
from telethon import TelegramClient
from telethon.sessions import StringSession

user_client: TelegramClient = None  # type: ignore

api_hash = os.environ.get('API_HASH')
api_id = os.environ.get('API_ID')
session_string = os.environ.get('SESSION_STRING')

if not api_hash or not api_id or not session_string:
    raise Exception('API_HASH or API_ID or SESSION_STRING has not been set!')


async def getUserClient():
    global user_client
    if not user_client:
        user_client = TelegramClient(
            StringSession(session_string), api_hash=api_hash, api_id=int(api_id))
        await user_client.connect()
    return user_client
