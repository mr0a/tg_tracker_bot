import asyncio
import json
from tortoise import Tortoise, run_async
import logging
import os
from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from models import User, Trackers, ChannelTracker
import dataProviders
from scheduler import scheduler
from apscheduler.triggers.cron import CronTrigger
from bot import getBotClient
from utils import send_message, startListener
from account import getUserClient
from telethon import events


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

router = Router()


@router.message(Command(commands=['start']))
async def start_handler(message: Message) -> None:
    if message.from_user:
        await message.answer(f'Hello {message.from_user.full_name}!')
        user = await User(chat_id=message.from_user.id, user_name=message.from_user.username or message.from_user.full_name)
        if await user.exists(chat_id=message.from_user.id):
            await message.answer("Welcom Back!")
        else:
            await user.save()


@router.message(Command(commands=['track']))
async def track_handler(message: Message) -> None:
    if message.text and message.from_user:
        args = message.text.split()
        if len(args) < 4:
            await message.answer("To track any items send its name, time interval and tick as in below format!")
            await message.answer('/track btc 5m 5000 bitcoivaTrack')
            await message.answer('The above would help me to track btc with 5 minute interval and \
                                let you know the price when its price changes by Rs. 5000. The last argument is the name of the function \
                                to use to get the price.')
            return

        user = await User.get_or_none(chat_id=message.from_user.id)
        if not user:
            await message.answer("Run /start first!")
            return
        tracker = await Trackers(user=user, token_name=args[1], time_interval=args[2], price_tick=args[3], executor=args[4])
        print(tracker)
        await tracker.save()
        func = getattr(dataProviders, args[4])
        minutes = args[2][:-1]
        scheduler.add_job(func, id=args[1] + args[4], trigger='cron', minute=f'*/{minutes}', args=(tracker.token_name, tracker.price_tick,  # type: ignore
                                                                                                   user.chat_id))
        await message.reply('I am tracking it for you!')


@router.message(Command(commands=['getdata']))
async def getData_handler(message: Message) -> None:
    if not message.text or not message.from_user:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("To get data by calling a function give in below format!")
        await message.answer('/getdata getBitcoivaData BDX_INR')
        await message.answer('I will send the output of the given function with following values as argument')
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        await message.answer("Run /start first!")
    else:
        func = getattr(dataProviders, args[1])
        data = await func(*args[2:])
        await send_message(message.from_user.id, 'The following is the latest data:' + json.dumps(data, indent=4))


@router.message(Command(commands=['list']))
async def list_handler(message: Message) -> None:
    if not message.from_user:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        await message.answer("Run /start first!")
        return

    tracker = await Trackers.filter(user=user).all()
    reply = ""
    for index, item in enumerate(tracker):
        reply += f"{index + 1}. {item.token_name} {item.time_interval} Rs. {item.price_tick}"
    if not tracker:
        await message.reply("No trackers found!")
        return
    await message.reply(reply)


@router.message(Command(commands=['delete']))
async def delete_handler(message: Message) -> None:
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        await message.answer("Run /start first!")
        return

    tracker = await Trackers.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        message.reply("Id of the tracker to delete is missing")
        return
    if int(args[1]) > len(tracker):
        message.reply("Id of the tracker is invalid")
        return
    toBeDeleted: Trackers = tracker[int(args[1]) - 1]
    scheduler.remove_job(toBeDeleted.token_name + toBeDeleted.executor)
    await toBeDeleted.delete()
    await toBeDeleted.save()
    await message.reply("The tracker has been deleted successfully!")


@router.message(Command(commands=['pause']))
async def pause_handler(message: Message):
    if not message.from_user or not message.text:
        return
    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")
    tracker = await Trackers.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        return message.reply("Id of the tracker to delete is missing")
    if int(args[1]) > len(tracker):
        return message.reply("Id of the tracker is invalid")
    toBePaused: Trackers = tracker[int(args[1]) - 1]
    scheduler.pause_job(toBePaused.token_name + toBePaused.executor)
    await message.reply("The tracker has been Paused successfully!")


@router.message(Command(commands=['resume']))
async def resume_handler(message: Message):
    if not message.from_user or not message.text:
        return
    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")
    tracker = await Trackers.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        return message.reply("Id of the tracker to delete is missing")
    if int(args[1]) > len(tracker):
        return message.reply("Id of the tracker is invalid")
    toBeResumed: Trackers = tracker[int(args[1]) - 1]
    scheduler.resume_job(toBeResumed.token_name + toBeResumed.executor)
    await message.reply("The tracker has been Resumed successfully!")


@router.message(Command(commands=['trackUnjoinedChannel']))
async def trackUnjoinedChannel(message: Message):
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")

    args = message.text.split()
    args.pop(0)  # Removing the command input
    print(message.text)
    if len(args) < 7:
        return message.reply("Invalid number of args! You need to send channel name and cron expression to track")
    channelName = args.pop(0)
    cron_expression = ' '.join(args)
    cron_seconds = args.pop(0)
    cron_minutes = args.pop(0)
    cron_hours = args.pop(0)
    cron_day = args.pop(0)
    cron_month = args.pop(0)
    cron_day_of_week = args.pop(0)

    try:
        client = await getUserClient()
        print("Got client", client)
        group = await client.get_peer_id(channelName)
    except ValueError as exc:
        await message.reply("Invalid channel name!")
        return
    tracker, created = await ChannelTracker.get_or_create(channel_id=channelName, user=user, cron_interval=cron_expression)
    print(tracker)
    print(created)
    if created:
        try:
            cronTrigger = CronTrigger(second=cron_seconds, minute=cron_minutes, hour=cron_hours,
                                      day=cron_day, day_of_week=cron_day_of_week, month=cron_month, timezone='Asia/Kolkata')
            func = getattr(dataProviders, 'unjoinedChannelTrack')
            scheduler.add_job(func, id=channelName + str(user.chat_id),
                              trigger=cronTrigger,
                              args=(channelName, user.chat_id))
        except Exception as e:
            print(e)
            await tracker.delete()


@router.message(Command(commands=['listChannelTracker']))
async def listChannelTracker_handler(message: Message):
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")

    trackers = await ChannelTracker.filter(user=user).all()
    if trackers:
        reply = ""
        for index, item in enumerate(trackers):
            reply += f"{index + 1}. {item.channel_id} {item.cron_interval} Rs. {item.pattern}"
        await message.reply(reply)
    else:
        await message.reply("No trackers found!")


@router.message(Command(commands=['deleteChannelTracker']))
async def deleteChannel_handler(message: Message) -> None:
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        await message.answer("Run /start first!")
        return

    tracker = await ChannelTracker.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        message.reply("Id of the tracker to delete is missing")
        return
    if int(args[1]) > len(tracker):
        message.reply("Id of the tracker is invalid")
        return
    toBeDeleted: ChannelTracker = tracker[int(args[1]) - 1]
    scheduler.remove_job(toBeDeleted.channel_id + str(user.chat_id))
    await toBeDeleted.delete()
    await toBeDeleted.save()
    await message.reply("The tracker has been deleted successfully!")


@router.message(Command(commands=['pauseChannelTracker']))
async def pauseChannel_tracker(message: Message):
    if not message.from_user or not message.text:
        return
    user = await User.get_or_none(chat_id=message.from_user.id)

    if not user:
        return await message.answer("Run /start first!")

    tracker = await ChannelTracker.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        return message.reply("Id of the tracker to delete is missing")
    if int(args[1]) > len(tracker):
        return message.reply("Id of the tracker is invalid")
    toBePaused: ChannelTracker = tracker[int(args[1]) - 1]
    scheduler.pause_job(toBePaused.channel_id + str(user.chat_id))
    await message.reply("The tracker has been Paused successfully!")


@router.message(Command(commands=['resumeChannelTracker']))
async def resumeChannel_handler(message: Message):
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")

    tracker = await ChannelTracker.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        return message.reply("Id of the tracker to delete is missing")
    if int(args[1]) > len(tracker):
        return message.reply("Id of the tracker is invalid")

    toBeResumed: ChannelTracker = tracker[int(args[1]) - 1]
    scheduler.resume_job(toBeResumed.channel_id + str(user.chat_id))
    await message.reply("The tracker has been Resumed successfully!")


async def handler(event, chat_id):
    await send_message(chat_id, event.message.message)


@router.message(Command(commands=['trackJoinedChannel']))
async def trackJoinedChannel(message: Message):
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")

    args = message.text.split()
    print(message.text)
    args.pop(0)  # Removing the command input
    channelName = args.pop(0)
    pattern = args.pop(0)
    try:
        client = await getUserClient()
        await client.get_peer_id(channelName)
    except ValueError as exc:
        await message.reply("Invalid channel name!")
        return
    # tracker, created = await ChannelTracker.get_or_create(channel_id=channelName, user=user, cron_interval='')
    # print(tracker)
    client.add_event_handler(
        lambda event: handler(event, user.chat_id), events.NewMessage(chats=[channelName], pattern=fr'(?i).*{pattern}'))
    await startListener()
    logging.info("Successfully added joined channel tracker")
    print(client.list_event_handlers())


@router.message(Command(commands=['clearJoinedChannel']))
async def clearJoinedChannel(message: Message):
    if not message.from_user or not message.text:
        return

    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")

    args = message.text.split()
    print(message.text)
    client = await getUserClient()
    client.remove_event_handler(lambda event: handler(event, user.chat_id))


async def init_db():
    print("Calling init_db")
    db_url = os.environ.get(
        'DATABASE_URL', 'sqlite:///Users/aravindhan/Workspace/TeleBot/db.sqlite')
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()


async def main():
    await init_db()
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    # trackersData = await Trackers.all()
    # for tracker in trackersData:
    #     print(tracker)
    #     user = await tracker.user
    #     print(user)
    # await bitcoivaTrack(tracker.token_name, tracker.price_tick, tracker.user.chat_id, bot.send_message)
    scheduler.start()
    await dispatcher.start_polling(getBotClient())
    print("Completed Main")


if __name__ == "__main__":
    run_async(main())
