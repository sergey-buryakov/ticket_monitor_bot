from client import utils
from enum import Enum


class Station:

    def __init__(self, id, title):
        self.id = id
        self.title = title

    def __str__(self):
        return self.title

    @classmethod
    def from_json(cls, json):
        return cls(json['value'], json['title'])


class Train:

    def __init__(self, num, category, is_transformer, travel_time, wagon_types, from_station, to_station,
                 departure_date, departure_time, arrival_date, arrival_time):
        self.num = num
        self.category = category
        self.is_transformer = is_transformer
        self.travel_time = travel_time
        self.wagon_types = wagon_types
        self.from_station = from_station
        self.to_station = to_station
        self.departure_date = departure_date
        self.departure_time = departure_time
        self.arrival_date = arrival_date
        self.arrival_time = arrival_time
        self.has_free_places = len(wagon_types) != 0

    def __str__(self):
        result = '{}: {} - {}\n{} {}\n{} {}\n'.format(
            self.num,
            self.from_station,
            self.to_station,
            self.departure_date,
            self.departure_time,
            self.arrival_date,
            self.arrival_time)
        if self.has_free_places:
            for wagon in self.wagon_types:
                result += str(wagon)
        return result

    @classmethod
    def from_json(cls, json):
        return cls(
            num=json['num'],
            category=json['category'],
            is_transformer=json['isTransformer'],
            travel_time=json['travelTime'],
            wagon_types=[WagonType.from_json(i) for i in json['types']],
            from_station=Station(json['from']['code'],
                                 json['from']['station']),
            to_station=Station(json['to']['code'],
                               json['to']['station']),
            departure_date=utils.convert_date_to_isoformat(json['from']['date']),
            departure_time=json['from']['time'],
            arrival_date=utils.convert_date_to_isoformat(json['to']['date']),
            arrival_time=json['to']['time']
        )


class WagonType:

    def __init__(self, letter, places, title):
        self.letter = letter
        self.places = places
        self.title = title

    def __str__(self):
        return '%s: %s (%s)\n' % (self.letter, self.places, self.title)

    @classmethod
    def from_json(cls, json):
        if json == []:
            return []
        return cls(*(json[i] for i in ('letter', 'places', 'title')))


class Wagon:

    def __init__(self, num, type, klass, free_places, has_bedding, services, prices, reserve_price, allow_bonus):
        self.num = num
        self.type = type
        self.klass = klass
        self.free_places = free_places
        self.has_bedding = has_bedding
        self.services = services
        self.prices = prices
        self.reserve_price = reserve_price
        self.allow_bonus = allow_bonus

    def __str__(self):
        return 'Wagon %s with free places: %d' % (self.num, self.free_places)

    @classmethod
    def from_json(cls, json):
        return cls(
            num=json['num'],
            type=json['type'],
            klass=json['class'],
            free_places=json['free'],
            has_bedding=json['hasBedding'],
            services=json['services'],
            prices=json['prices'],
            reserve_price=json['reservePrice'],
            allow_bonus=json['allowBonus'])


class States(Enum):
    SOURCE_STATION_REQUESTED = 0
    SOURCE_STATION_LIST_SHOWED = 1
    DEST_STATION_REQUESTED = 2
    DEST_STATION_LIST_SHOWED = 3
    DATE_REQUESTED = 4


class User:
    pass


