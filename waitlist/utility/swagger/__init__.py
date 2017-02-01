from pyswagger import App
from datetime import datetime
from email._parseaddr import mktime_tz
from email.utils import parsedate_tz


api = App._create_('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')


def header_to_datetime(header) -> datetime:
    return datetime.fromtimestamp(mktime_tz(parsedate_tz(header)))
