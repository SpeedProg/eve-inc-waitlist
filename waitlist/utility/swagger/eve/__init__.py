from esipy.security import EsiSecurity
from waitlist.utility.swagger import api, header_to_datetime
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from flask_login import current_user
from esipy.client import EsiClient
from datetime import datetime

def get_expire_time(response):
    # type: (Any) -> datetime
    cacheTime = header_to_datetime(response.header['Expires'][0])
    return header_to_datetime(cacheTime)

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

def get_esi_client():
    # type: () -> EsiClient
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires - datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })
    client = EsiClient(security)
    return client