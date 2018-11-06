import requests
from itertools import chain
from ticket_monitor_bot.client.models import Train, Station, Wagon
from ticket_monitor_bot.client.exeptions import HTTPError, ResponseError


class Client:

    def __init__(self):
        self.__base_address = 'https://booking.uz.gov.ua/'

    def __build_headers(self):
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.__base_address
        }

    def __perform_request(self, endpoint, data={}, params={}):
        full_url = self.__base_address + endpoint
        resp = requests.post(full_url, data=data, params=params)
        if not resp.status_code == 200:
            raise HTTPError(resp.status_code, data, resp.text)
        json = resp.json()
        if 'error' in json:
            raise ResponseError(resp.status_code, data, json['data'])
        return json

    def search_stations(self, name):
        response = self.__perform_request(endpoint='train_search/station/', params={"term": name})
        return [Station.from_json(i) for i in response]

    def get_first_station(self, station):
        stations = self.search_stations(station)
        return stations and stations[0] or None

    def search_trains(self, source_station, dest_station, date):
        data = {
            'from': source_station.id,
            'to': dest_station.id,
            'date': date,
            'time': '00:00'
        }
        response = self.__perform_request(endpoint='train_search/', data=data)
        return [Train.from_json(i) for i in response['data']['list']]

    def load_wagons(self, train, wagon_type):
        data = {
            'date':	train.departure_date,
            'from':	train.from_station.id,
            'to': train.to_station.id,
            'train': train.num,
            'wagon_type_id': wagon_type.letter
        }
        response = self.__perform_request(endpoint='train_wagons/', data=data)
        return [Wagon.from_json(i) for i in response['data']['wagons']]

    def load_places(self, train, wagon):
        data = {
            'date':	train.departure_date,
            'from':	train.from_station.id,
            'to': train.to_station.id,
            'train': train.num,
            'wagon_class': wagon.klass,
            'wagon_num': wagon.num,
            'wagon_type': wagon.type
        }
        response = self.__perform_request(endpoint='train_wagon/', data=data)
        return list(chain(*response['data']['places'].values()))
