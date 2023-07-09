import asyncio
from account import getUserClient
from bot import getBotClient


async def send_message(chat_id, message):
    botApp = getBotClient()
    if len(message) > 4095:
        for x in range(0, len(message), 4095):
            await botApp.send_message(chat_id, text=message[x:x+4095])
    else:
        await botApp.send_message(chat_id, message)


async def get_messages(entity, **kargs):
    client = await getUserClient()
    messages = await client.get_messages(entity, **kargs)
    return messages

executed = False


async def startListener():
    global executed
    if not executed:
        client = await getUserClient()
        client.loop.create_task(
            client.run_until_disconnected())  # type: ignore
        executed = True
