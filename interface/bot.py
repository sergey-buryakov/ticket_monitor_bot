import os
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.types.message import ContentType
from client.models import User, States
from interface import utils

# Configure logging
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = {}


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
    users[message.chat.id] = user
    keyboard = utils.remove_keyboard()
    await bot.send_message(message.chat.id, "Напиши станцію відправлення!\nНаприклад: Київ", reply_markup=keyboard)


@dp.message_handler(func=lambda message: message.chat.id in users, content_types=ContentType.TEXT)
async def send_resp(message):
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

    else:
        msg = "WTF"  # for debug

    await bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
