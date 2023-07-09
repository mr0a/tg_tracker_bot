import os
from telethon import TelegramClient

api_hash = os.environ.get('API_HASH')
api_id = os.environ.get('API_ID')

if not api_id or not api_hash:
    raise Exception('API_HASH or API_ID has not been set')

with TelegramClient('anon_main', int(api_id), api_hash) as client:
    client.loop.run_until_complete(client.send_message(
        'me', 'Hello, Session has been generated!'))
