from pyswagger import App
from typing import Any, Optional

from esipy.security import EsiSecurity
from waitlist.utility.swagger import header_to_datetime, get_api
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from flask_login import current_user
from datetime import datetime, timezone
from waitlist.storage.database import Account
from waitlist.utility.swagger.patch import EsiClient


def get_expire_time(response: Any) -> datetime:
    if 'Expires' in response.header:
        return header_to_datetime(response.header['Expires'][0])
    return datetime.utcnow()


class ESIEndpoint(object):
    def __init(self):
        pass

    def _add_esi_api(self, version: str) -> None:
        self.__dict__['api_'+version] = get_api(version)

    def _api(self, version: str) -> App:
        return self.__dict__['api_'+version]

    @staticmethod
    def is_endpoint_available(api: App, endpoint_name: str) -> bool:
        return endpoint_name in api.op

    def __try_reload_api(self, version: str):
        self.__dict__['api_' + version] = get_api(version)


class ESIResponse(object):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str]) -> None:
        self.__expires: datetime = expires
        self.__status_code: int = status_code
        self.__error: str = error

    @staticmethod
    def parse_datetime(datetime_string: str):
        dt = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
        dt.replace(tzinfo=timezone.utc)
        return dt

    def expires(self) -> datetime:
        return self.__expires

    def code(self) -> int:
        return self.__status_code

    def is_error(self) -> bool:
        if self.__error is None:
            return False
        return True

    def error(self) -> Optional[str]:
        return self.__error


def make_error_response(resp: Any):
    msg = resp.data['error'] if 'error' in resp.data else 'No error data send'
    return ESIResponse(get_expire_time(resp), resp.status, msg)


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
