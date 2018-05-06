import ast
import json
import logging
from pyswagger import App
from typing import Any, Optional

from esipy.security import EsiSecurity

from waitlist.data.version import version
from waitlist.utility.swagger import header_to_datetime, get_api
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from flask_login import current_user
from datetime import datetime, timezone
from waitlist.storage.database import Account
from waitlist.utility.swagger.patch import EsiClient

logger = logging.getLogger(__name__)


def get_expire_time(response: Any) -> datetime:
    if 'Expires' in response.header:
        return header_to_datetime(response.header['Expires'][0])
    return datetime.utcnow()


class ESIEndpoint(object):
    def __init__(self):
        self.__api: App = None

    def _api(self) -> App:
        if self.__api is None:
            self.__api: App = get_api()
        return self.__api


class ESIResponse(object):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str]) -> None:
        self.__expires: datetime = expires
        self.__status_code: int = status_code
        self.__error: str = error

    def expires(self) -> datetime:
        return self.__expires

    def code(self) -> int:
        return self.__status_code

    def is_error(self) -> bool:
        if self.__error is None:
            return False
        return True

    def is_monolith_error(self):
        if self.is_error():
            if self.__status_code == 520:
                if 'error_label' in self.__error:
                    return True
                else:
                    logger.error(f"Unknown Monolith error format: {self.__error}")
        return False

    def get_monolith_error(self):
        return ast.literal_eval(self.__error)

    def error(self) -> Optional[str]:
        return self.__error


def make_error_response(resp: Any) -> ESIResponse:
    if resp.status == 520:  # monolith error
        if resp.data is None:
            data = json.loads(resp.raw.decode("utf-8"))
            msg = data['error'] if data is not None and 'error' in data else 'No error data send'
        elif resp.data is not None and 'error' in resp.data:
            msg = resp.data['error']
        else:
            msg = f'Unknown Monolith error {resp.data}'
    else:
        msg = resp.data['error'] if resp.data is not None and 'error' in resp.data else 'No error data send'
    logger.error(f'ESI responded with status {resp.status} and msg {msg}')
    return ESIResponse(get_expire_time(resp), resp.status, msg)


def get_esi_client(noauth: bool = False) -> EsiClient:
    return get_esi_client_for_account(current_user, noauth)


def get_esi_client_for_account(account: Account, noauth: bool = False) -> EsiClient:
    if noauth:
        return EsiClient(timeout=10, headers={'User-Agent': 'Bruce Warhead IncWaitlist/'+version})

    security = EsiSecurity(
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': account.sso_token.access_token,
        'expires_in': (account.sso_token.access_token_expires -
                       datetime.utcnow()).total_seconds(),
        'refresh_token': account.sso_token.refresh_token
    })
    return EsiClient(security, timeout=10, headers={'User-Agent': 'Bruce Warhead IncWaitlist/'+version})
