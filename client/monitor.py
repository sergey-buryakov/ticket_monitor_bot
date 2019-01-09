import asyncio
import random
import logging
from uuid import uuid4
from client.uzclientasync import Client


logger = logging.getLogger('uzmonitor')


class Monitor(object):

    def __init__(self, success_cb, delay=360):
        self.success_cb = success_cb

        self.loop = asyncio.get_event_loop()
        self.delay = delay
        self.client = Client()
        self.__state = dict()
        self.__running = False

    async def run(self):
        logger.info('Starting Monitor')
        self.__running = True
        while self.__running:
            logger.info('Starting iteration')
            for scan_id, data in self.__state.items():
                asyncio.create_task(self.scan(scan_id, data))
            await asyncio.sleep(self.delay * random.randint(1, 6))

    def stop(self):
        logger.info('Stopping Monitor')
        self.__running = False

    def add_item(self, success_cb_id, date, source, destination, train_num=None, wagon_letters=None):
        scan_id = uuid4().hex[:8]
        logger.info('Adding monitor with id={}'.format(scan_id))
        self.__state[scan_id] = dict(
            success_cb_id=success_cb_id,
            date=date,
            source=source,
            destination=destination,
            train_num=train_num,        # for future
            wagon_letters=wagon_letters,
            lock=asyncio.Lock())
        return scan_id

    def delete(self, scan_id):
        if scan_id in self.__state:
            logger.info('Deleting monitor with id={}'.format(scan_id))
            del self.__state[scan_id]
            return True
        raise UnknownScanID(scan_id)

    @staticmethod
    def find_wagon_type(train, wagon_letter):
        for wagon_type in train.wagon_types:
            if wagon_type.letter == wagon_letter:
                return wagon_type

    async def scan(self, scan_id, data):
        if data['lock'].locked():
            return

        async with data['lock']:
            valid_trains = []
            trains = await self.client.search_trains(data['source'], data['destination'], data['date'])

            for train in trains:
                if train.has_free_places:
                    if data['wagon_letters']:
                        has_requested_types = False
                        for wagon_letter in data['wagon_letters']:
                            wagon_type = self.find_wagon_type(train, wagon_letter)
                            if wagon_type is not None:
                                has_requested_types = True
                        if not has_requested_types:
                            continue
                    logger.info('Find ticket')
                    valid_trains.append(train)
            if valid_trains:
                await self.success_cb(data['success_cb_id'], valid_trains, scan_id)


class UnknownScanID(Exception):
    pass
