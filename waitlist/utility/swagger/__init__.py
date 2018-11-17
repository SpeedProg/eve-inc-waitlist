from pyswagger import App
from datetime import datetime
from email._parseaddr import mktime_tz
from email.utils import parsedate_tz


cached_api: App = None


def header_to_datetime(header) -> datetime:
    return datetime.fromtimestamp(mktime_tz(parsedate_tz(header)))


def get_api() -> App:
    global cached_api
    if cached_api is None:
        cached_api = App.create('static/swagger.json')
    return cached_api
