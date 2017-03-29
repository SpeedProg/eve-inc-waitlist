from typing import Any, Optional

from esipy.security import EsiSecurity
from waitlist.utility.swagger import header_to_datetime, get_api
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from flask_login import current_user
from datetime import datetime
from waitlist.storage.database import Account
from waitlist.utility.swagger.patch import EsiClient


def get_expire_time(response: Any) -> datetime:
    if 'Expires' in response.header:
        return header_to_datetime(response.header['Expires'][0])
    return datetime.utcnow()


class ESIResponse(object):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str]) -> None:
        self.__expires = expires
        self.__status_code = status_code
        self.__error = error

    def expires(self) -> datetime:
        return self.__expires

    def code(self) -> int:
        return self.__status_code

    def is_error(self) -> bool:
        if self.__error is None:
            return False
        return True

    def error(self) -> str:
        return self.__error


def get_esi_client(version: str, noauth: bool = False) -> EsiClient:
    return get_esi_client_for_account(current_user, version, noauth)


def get_esi_client_for_account(account: Account, version: str, noauth: bool = False) -> EsiClient:
    if noauth:
        return EsiClient(timeout=10)

    security = EsiSecurity(
        get_api(version),
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': account.ssoToken.access_token,
        'expires_in': (account.ssoToken.access_token_expires -
                       datetime.utcnow()).total_seconds(),
        'refresh_token': account.ssoToken.refresh_token
    })
    return EsiClient(security, timeout=10)
