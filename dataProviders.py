import time
import aiohttp
import json
import pprint
from telethon.types import Message
from utils import send_message
from utils import get_messages
from models import ChannelTracker


async def getBitcoivaData(symbol):
    from_time = round(time.time()) - 60 * 30    # 30 Mins before
    to_time = round(time.time())    # Now
    print("Symbol", symbol)
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "origin": "https://bitcoiva.com",
        "referrer": "https://bitcoiva.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    async with aiohttp.ClientSession(base_url='https://rtrxastzeqsaoqd.bitcoiva.com', headers=headers) as session:
        response = await session.get(f'/trading/chart/history?symbol={symbol}&resolution={5}&from={from_time}&to={to_time}')
        content = (await response.content.read()).decode()
        print(content)
        json_data = json.loads(content)
        return json_data


async def bitcoivaTrack(symbol, alert_price, chat_id):
    json_data = await getBitcoivaData(symbol)
    difference = max(json_data.get('h')) - min(json_data.get('l'))
    if difference >= alert_price:
        await send_message(chat_id, "Price has reached the alert level: \n" +
                           json.dumps(json_data, indent=4))


async def unjoinedChannelTrack(channel_name, chat_id):
    tracker = await ChannelTracker.get_or_none(channel_id=channel_name, user=chat_id)
    if not tracker:
        return
    if tracker.last_tracked_id is None:
        messages = await get_messages(entity=channel_name)
    else:
        messages = await get_messages(entity=channel_name, min_id=tracker.last_tracked_id, limit=10, reverse=True)
    # print(messages)
    print("Messages length is ", len(messages))
    if len(messages) == 0:
        return

    tracker.last_tracked_id = messages[-1].id
    await tracker.save()
    for message in messages:
        assert isinstance(message, Message)
        message_from = message.post_author or channel_name
        await send_message(chat_id, "Message from " + message_from)
        if message.media:
            await send_message(chat_id, "This message has a file")
        if message.message:
            await send_message(chat_id, message.message)
