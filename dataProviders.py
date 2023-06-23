import time
import aiohttp
import json
import pprint
from bot import send_message


async def getBitcoivaData(symbol):
    from_time = round(time.time()) - 60 * 30    # 30 Mins before
    to_time = round(time.time())    # Now
    print("Symbol", symbol)
    async with aiohttp.ClientSession(base_url='https://chart.bitcoiva.com') as session:
        response = await session.get(f'/tradeChart/chart/history?symbol={symbol}&resolution={5}&from={from_time}&to={to_time}')
        content = (await response.content.read()).decode()
        json_data = json.loads(content)
        return json_data


async def bitcoivaTrack(symbol, alert_price, chat_id):
    json_data = await getBitcoivaData(symbol)
    difference = max(json_data.get('h')) - min(json_data.get('l'))
    if difference >= alert_price:
        await send_message(chat_id, "Price has reached the alert level: \n" +
                           json.dumps(json_data, indent=4))
