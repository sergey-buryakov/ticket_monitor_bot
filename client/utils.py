from datetime import datetime


def convert_date_to_isoformat(date):
    return datetime.strptime(str.split(date)[1], '%d.%m.%Y').date().isoformat()
