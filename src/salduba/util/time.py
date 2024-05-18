import datetime


def millis_epoch(t: datetime.datetime = datetime.datetime.now()) -> int:
    return int(t.timestamp() * 1000)


ninety_days = 90 * 24 * 60 * 60 * 1000
