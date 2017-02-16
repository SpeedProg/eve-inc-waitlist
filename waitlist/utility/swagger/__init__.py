from pyswagger import App
from datetime import datetime
from email._parseaddr import mktime_tz
from email.utils import parsedate_tz


def header_to_datetime(header) -> datetime:
    return datetime.fromtimestamp(mktime_tz(parsedate_tz(header)))

apis = {}


def get_api(version: str) -> App:
    if version in apis:
        return apis[version]

    api = App.create('https://esi.tech.ccp.is/'+version+'/swagger.json')
    apis[version] = api
    return apis[version]
