import asyncio
import logging
from itertools import chain
import aiohttp
from client.models import Train, Station, Wagon
from client.exeptions import HTTPError, ResponseError


class Client:

    def __init__(self):
        self.__base_address = 'https://booking.uz.gov.ua/'

    def __build_headers(self):
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.__base_address
        }

    async def __perform_request(self, endpoint, data={}, params={}):
        full_url = self.__base_address + endpoint
        logging.info("Ready to send request")
        async with aiohttp.ClientSession(headers=self.__build_headers()) as session:
            logging.info("session is established")
            async with session.post(full_url, params=params, data=data) as resp:
                logging.info("Request has been sent to {}".format(full_url))
                if not resp.status == 200:
                    try:
                        json = await resp.json()
                    except aiohttp.ContentTypeError:
                        json = None
                    raise HTTPError(resp.status, data, json)
                json = await resp.json()
                if 'error' in json:
                    raise ResponseError(resp.status, data, json)
                return json

    async def search_stations(self, name):
        response = await self.__perform_request(endpoint='train_search/station/', params={"term": name})
        return [Station.from_json(i) for i in response]

    async def get_first_station(self, station):
        stations = await self.search_stations(station)
        return stations[0] if stations else None

    async def search_trains(self, source_station, dest_station, date):
        data = {
            'from': source_station.id,
            'to': dest_station.id,
            'date': date,
            'time': '00:00'
        }
        response = await self.__perform_request(endpoint='train_search/', data=data)
        return [Train.from_json(i) for i in response['data']['list']]

    async def load_wagons(self, train, wagon_type):
        data = {
            'date':	train.departure_date,
            'from':	train.from_station.id,
            'to': train.to_station.id,
            'train': train.num,
            'wagon_type_id': wagon_type.letter
        }
        response = await self.__perform_request(endpoint='train_wagons/', data=data)
        return [Wagon.from_json(i) for i in response['data']['wagons']]

    async def load_places(self, train, wagon):
        data = {
            'date':	train.departure_date,
            'from':	train.from_station.id,
            'to': train.to_station.id,
            'train': train.num,
            'wagon_class': wagon.klass,
            'wagon_num': wagon.num,
            'wagon_type': wagon.type
        }
        response = await self.__perform_request(endpoint='train_wagon/', data=data)
        return list(chain(*response['data']['places'].values()))


async def main():
    client = Client()
    station = input("Enter station: ")

    s_stations = await client.search_stations(station)
    for i in s_stations:
        print(i)
    print()
    s_station = s_stations[int(input("Enter number: "))]

    print()
    station = input("Enter station: ")

    d_stations = await client.search_stations(station)
    for i in d_stations:
        print(i)
    print()
    d_station = d_stations[int(input("Enter number: "))]

    print()
    date = input("Enter date in format YYYY-MM-DD: ")

    print()
    trains = await client.search_trains(s_station, d_station, date)
    for i in trains:
        print(i)
    print()
    train = trains[int(input("Enter number: "))]

    print()
    for i in train.wagon_types:
        print(i)
    print()
    wagon_type = train.wagon_types[int(input("Enter number: "))]

    print()
    wagons = await client.load_wagons(train, wagon_type)
    for i in wagons:
        print(i)
    wagon = wagons[int(input("Enter number: "))]

    print()
    seats = await client.load_places(train, wagon)
    for seat in sorted(seats):
        print(seat)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
