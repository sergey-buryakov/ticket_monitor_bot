import re
from datetime import date as Date
from aiogram import types
from client.uzclientasync import Client


CLIENT = Client()


def date_check(date_str, user):
    r_date = re.fullmatch(r"^\d\d\.\d\d$", date_str)
    msg = ""
    if r_date is None:
        msg = "Вкажи дату поїздки в правильному форматі день.місяць (наприклад 01.02)"
        return msg
    try:
        day, month = r_date.string.split(".")
        day = int(day)
        month = int(month)
        date = Date(Date.today().year, month, day)
        if Date.today() > date:
            date = Date(Date.today().year+1, month, day)
        user.date = date.isoformat()
    except ValueError:
        msg = "Вкажи коректну дату!"
    return msg


async def get_trains(user):
    msg = ""
    trains = await CLIENT.search_trains(user.source_station, user.dest_station, user.date)
    for train in trains:
        if train.has_free_places:
            msg += parse_train(train) + "\n"
    if msg == "":
        msg = "Квитків не знайдено :(\nМожеш спробувати ввести іншу дату"
    return msg


def parse_train(train):
    result = '*{}: {} - {}*\n' \
             'Відправлення: {} {}\n' \
             'Прибуття: {} {}\n' \
             'Час в дорозі: {}\n'.format(train.num, train.from_station, train.to_station, train.departure_date, train.departure_time, train.arrival_date, train.arrival_time, train.travel_time)
    if train.has_free_places:
        for wagon in train.wagon_types:
            result += "[{}]({})".format(str(wagon), create_link(train, wagon))
    return result


def create_link(train, wagon_type):
    return "https://booking.uz.gov.ua/?from={}&to={}&date={}&time=00%3A00&train={}&wagon_type_id={}&url=train-wagons".format(
        train.from_station.id,
        train.to_station.id,
        train.departure_date,
        train.num,
        wagon_type.letter
    )


def set_station(name_station, user, next_state, direction, success_msg):
    result = None
    msg = ""
    keyboard = None
    for station in user.stations:
        if station.title == name_station:
            result = station
            msg = "Станція {}: {}\n\n{}".format(direction, str(station), success_msg)
            user.state = next_state
            keyboard = remove_keyboard()
    if result is None:
        msg = "Обери станцію з переліку або почни з початку /search"

    return msg, result, keyboard


async def get_list_stations(name_station, user, next_state, success_msg):
    keyboard = None
    user.stations = await CLIENT.search_stations(name_station)
    if not user.stations:
        msg = "Спробуй іншу станцію"
    else:
        keyboard = set_keyboard(user.stations)
        user.state = next_state
        msg = success_msg
    return msg, keyboard


def remove_keyboard():
    return types.ReplyKeyboardRemove()


def set_keyboard(items):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(str(item))
    return markup
