import logging
from itertools import chain
import aiohttp
from client.models import Train, Station, Wagon
from client.exeptions import HTTPError, ResponseError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("uzclient")


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
        logger.info("Ready to send request")
        async with aiohttp.ClientSession() as session:
            async with session.post(full_url, params=params, data=data, headers=self.__build_headers()) as resp:
                logger.info("Response received from {}".format(full_url))
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
