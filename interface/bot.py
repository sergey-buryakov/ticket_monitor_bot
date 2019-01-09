import os
import logging
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import filters
from aiogram.types.message import ContentType
from client.models import User, States
from interface import utils
from client.monitor import Monitor, UnknownScanID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('bot')

TOKEN = os.environ.get('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = {}
WAGON_TYPE_KEYBOARD = [{"wagon_К": "Купе", "wagon_П": "Плацкарт", "wagon_Л": "Люкс"}, {"wagon_С1": "C1", "wagon_С2": "С2", "wagon_С3": "С3"}, {"create_monitor": "Створити"}]


@dp.message_handler(commands=['check'])
async def check_connections(message):
    url = message.get_args()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            msg = resp.status
    await bot.send_message(message.chat.id, msg)


@dp.message_handler(commands=['start'])
async def send_welcome(message):
    msg = "Привіт!\n" \
          "Я бот для пошуку та моніторингу залізничних квитків.\n" \
          "Для того щоб перевіряти наявність квитків на вказаний маршрут введіть /search"
    await bot.send_message(message.chat.id, msg)


@dp.message_handler(commands=['search'])
async def search_command(message):
    user = User()
    user.state = States.SOURCE_STATION_REQUESTED
    user.monitors = []
    users[message.chat.id] = user
    keyboard = utils.remove_keyboard()
    await bot.send_message(message.chat.id, "Напиши станцію відправлення!\nНаприклад: Київ", reply_markup=keyboard)


@dp.message_handler(lambda message: message.chat.id in users, content_types=ContentType.TEXT)
async def set_trip(message):
    user = users[message.chat.id]
    keyboard = None
    if user.state == States.SOURCE_STATION_REQUESTED:
        msg, keyboard = await utils.get_list_stations(message.text, user, States.SOURCE_STATION_LIST_SHOWED, "Обери з переліку станцію відправлення.")

    elif user.state == States.SOURCE_STATION_LIST_SHOWED:
        msg, user.source_station, keyboard = utils.set_station(message.text, user, States.DEST_STATION_REQUESTED, "відправлення", "Напиши станцію прибуття!\nНаприклад: Одеса")

    elif user.state == States.DEST_STATION_REQUESTED:
        msg, keyboard = await utils.get_list_stations(message.text, user, States.DEST_STATION_LIST_SHOWED, "Обери з переліку станцію прибуття.")

    elif user.state == States.DEST_STATION_LIST_SHOWED:
        msg, user.dest_station, keyboard = utils.set_station(message.text, user, States.DATE_REQUESTED, "прибуття", "Вкажи дату поїздки в правильному форматі день.місяць (наприклад 01.02)")

    elif user.state == States.DATE_REQUESTED:
        msg = utils.date_check(message.text, user)
        if msg == "":
            await bot.send_message(message.chat.id, "Вибрана дата: {}\n\nВиконую пошук.\nМені потрібно кілька секунд...".format(user.date))
            msg = await utils.get_trains(user)
            user.state = States.SOURCE_STATION_REQUESTED
            keyboard = utils.set_callback_buttons([{"set_monitor": "Створити моніторинг", "otherdate": "Інша дата"}])

    else:
        msg = "WTF"  # for debug

    await bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True)


@dp.callback_query_handler(lambda call: call.data == "set_monitor")
async def set_monitor(call):
    user = users[call.message.chat.id]
    user.keyboard = WAGON_TYPE_KEYBOARD.copy()
    user.wagon_types = []
    keyboard = utils.set_callback_buttons(user.keyboard)
    await bot.send_message(call.message.chat.id, "Створення моніторингу квитків", reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.find("wagon_") != -1)
async def set_wagon_types(call):
    user = users[call.message.chat.id]
    wagon_type = call.data.replace("wagon_", "")
    for dict in user.keyboard:
        if call.data in dict:
            if wagon_type in user.wagon_types:
                user.wagon_types.remove(wagon_type)
                text = dict[call.data][:-1]
                dict[call.data] = text
            else:
                dict[call.data] += u"\u2705"
                user.wagon_types.append(wagon_type)
    keyboard = utils.set_callback_buttons(user.keyboard)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data == "create_monitor")
async def create_monitor(call):
    user = users[call.message.chat.id]
    if len(user.wagon_types) == 0:
        user.monitors = monitor.add_item(call.message.chat.id, user.date, user.source_station, user.dest_station)
    else:
        user.monitors = monitor.add_item(call.message.chat.id, user.date, user.source_station, user.dest_station, wagon_letters=user.wagon_types)
    await bot.send_message(call.message.chat.id, "Моніторинг успішно створено!")
    await bot.delete_message(call.message.chat.id, call.message.message_id)


@dp.callback_query_handler(lambda call: call.data == "otherdate")
async def set_other_date(call):
    user = users[call.message.chat.id]
    user.state = States.DATE_REQUESTED
    await bot.send_message(call.message.chat.id, "Вкажи дату поїздки в правильному форматі день.місяць (наприклад 01.02)")
    await call.answer()


# @dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['del_([0-9a-z]*)']))
@dp.callback_query_handler(lambda call: call.data.find("del_") != -1)
async def delete_monitor(call):
    scan_id = call.data.replace("del_", "")
    try:
        monitor.delete(scan_id)
        await call.answer(text="Моніторинг успішно видалено!")
    except UnknownScanID:
        await call.answer(text="Такий моніторинг більше не існує")


def ticket_cb(chat_id, trains, scan_id):
    msg = ""
    for train in trains:
        msg += utils.parse_train(train) + "\n"
    keyboard = utils.set_callback_buttons([{"del_" + scan_id: "Видалити моніторинг"}])
    return bot.send_message(chat_id, msg, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard)


if __name__ == '__main__':
    monitor = Monitor(ticket_cb)
    loop = asyncio.get_event_loop()
    loop.create_task(monitor.run())
    logger.info('Running...')
    try:
        executor.start_polling(dp, loop=loop, skip_updates=True)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
        logger.info('Shutting down...')
        logger.info('Waiting for all tasks to complete...')
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))
        loop.stop()
