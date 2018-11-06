import os
from telebot import TeleBot
from client.models import User, States
from interface import utils

TOKEN = os.environ.get('BOT_TOKEN')

bot = TeleBot(TOKEN)

users = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = "Привіт!\n" \
          "Я бот для пошуку та моніторингу залізничних квитків.\n" \
          "Для того щоб перевіряти наявність квитків на вказаний маршрут введіть /search"
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['search'])
def search_command(message):
    user = User()
    user.state = States.SOURCE_STATION_REQUESTED
    users[message.chat.id] = user
    keyboard = utils.remove_keyboard()
    bot.send_message(message.chat.id, "Напиши станцію відправлення!\nНаприклад: Київ", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.chat.id in users, content_types=['text'])
def send_resp(message):
    user = users[message.chat.id]
    keyboard = None
    if user.state == States.SOURCE_STATION_REQUESTED:
        msg, keyboard = utils.get_list_stations(message.text, user, States.SOURCE_STATION_LIST_SHOWED, "Обери з переліку станцію відправлення.")

    elif user.state == States.SOURCE_STATION_LIST_SHOWED:
        msg, user.source_station, keyboard = utils.set_station(message.text, user, States.DEST_STATION_REQUESTED,
                                               "відправлення", "Напиши станцію прибуття!\nНаприклад: Одеса")

    elif user.state == States.DEST_STATION_REQUESTED:
        msg, keyboard = utils.get_list_stations(message.text, user, States.DEST_STATION_LIST_SHOWED, "Обери з переліку станцію прибуття.")

    elif user.state == States.DEST_STATION_LIST_SHOWED:
        msg, user.dest_station, keyboard = utils.set_station(message.text, user, States.DATE_REQUESTED, "прибуття",
                          "Вкажи дату поїздки в правильному форматі день.місяць (наприклад 01.02)")

    elif user.state == States.DATE_REQUESTED:
        msg = utils.date_check(message.text, user)
        if msg == "":
            bot.send_message(message.chat.id, "Вибрана дата: {}\n\n"
                                              "Виконую пошук.\n"
                                              "Мені потрібно кілька секунд...".format(user.date))
            msg = utils.get_trains(user)

    else:
        msg = "WTF"  # for debug

    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True)


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=320)

