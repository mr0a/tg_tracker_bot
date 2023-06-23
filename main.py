from tortoise import Tortoise, run_async
import logging
import os
from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from models import User, Trackers
import dataProviders
from scheduler import scheduler
from bot import botApp


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

router = Router()


@router.message(Command(commands=['start']))
async def start_handler(message: Message) -> None:
    await message.answer(f'Hello {message.from_user.full_name}!')
    user = await User(chat_id=message.from_user.id, user_name=message.from_user.username or message.from_user.full_name)
    if await user.exists(chat_id=message.from_user.id):
        return await message.answer("Welcom Back!")
    await user.save()


@router.message(Command(commands=['track']))
async def start_handler(message: Message) -> None:
    print(message)
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
        return await message.answer("Run /start first!")
    tracker = await Trackers(user=user, token_name=args[1], time_interval=args[2], price_tick=args[3], executor=args[4])
    print(tracker)
    await tracker.save()
    func = getattr(dataProviders, args[4])
    minutes = args[2][:-1]
    scheduler.add_job(func, id=args[1] + args[4], trigger='cron', minute=f'*/{minutes}', args=(tracker.token_name, tracker.price_tick,
                                                                                               user.chat_id))
    await message.reply('I am tracking it for you!')


@router.message(Command(commands=['list']))
async def list_handler(message: Message) -> None:
    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")
    tracker = await Trackers.filter(user=user).all()
    reply = ""
    for index, item in enumerate(tracker):
        reply += f"{index + 1}. {item.token_name} {item.time_interval} Rs. {item.price_tick}"
    if not tracker:
        return await message.reply("No trackers found!")
    await message.reply(reply)


@router.message(Command(commands=['delete']))
async def delete_handler(message: Message) -> None:
    user = await User.get_or_none(chat_id=message.from_user.id)
    if not user:
        return await message.answer("Run /start first!")
    tracker = await Trackers.filter(user=user).all()
    args = message.text.split()
    if len(args) < 2:
        return message.reply("Id of the tracker to delete is missing")
    if int(args[1]) > len(tracker):
        return message.reply("Id of the tracker is invalid")
    toBeDeleted: Trackers = tracker[int(args[1]) - 1]
    scheduler.remove_job(toBeDeleted.token_name + toBeDeleted.executor)
    await toBeDeleted.delete()
    await toBeDeleted.save()
    await message.reply("The tracker has been deleted successfully!")


@router.message(Command(commands=['pause']))
async def pause_handler(message: Message):
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
async def pause_handler(message: Message):
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


@router.message()
async def init_db():
    await Tortoise.init(
        db_url=os.environ.get('DATABASE_URL'),
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
    await dispatcher.start_polling(botApp)


if __name__ == "__main__":
    run_async(main())
