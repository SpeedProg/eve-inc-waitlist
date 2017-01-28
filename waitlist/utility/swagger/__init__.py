from pyswagger import App
from datetime import datetime
api = App._create_('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')

def header_to_datetime(header):
    return datetime.fromtimestamp(mktime_tz(eut.parsedate_tz(header)))