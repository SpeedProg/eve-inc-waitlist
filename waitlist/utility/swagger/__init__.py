from pyswagger import App
from datetime import datetime
from email._parseaddr import mktime_tz
from email.utils import parsedate_tz
api = App._create_('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')

def header_to_datetime(header):
    return datetime.fromtimestamp(mktime_tz(parsedate_tz(header)))

class ESIResponse(object):
    def __init__(self, expires, status_code, error):
        # type: (expires) -> None
        self.__expires = expires
        self.__status_code
        self.__error = error
    
    def expires(self):
        # type: () -> datetime
        return self.__expires
    
    def code(self):
        # type: () -> int
        return self.__status_code
    
    def is_error(self):
        # type: () -> boolean
        if self.__error is None:
            return True
        return False
    
    def error(self):
        # type: () -> str
        return self.__error