import ast
import json
import logging
from datetime import datetime
from typing import Any, Optional

from esipy import EsiClient
from esipy.cache import DummyCache
from esipy.events import Signal
from esipy.security import EsiSecurity
from pyswagger import App

from waitlist.storage.database import SSOToken
from waitlist.utility import config
from waitlist.utility.config import crest_return_url, crest_client_id, \
    crest_client_secret
from waitlist.utility.swagger import header_to_datetime, get_api

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

    def __repr__(self):
        return f'<ESIResponse  code={self.code()} error={self.error()} expires={self.expires()}>'


def get_error_msg_from_response(resp: Any) -> str:
    if resp.status == 520:  # monolith error
        if resp.data is None:
            data = json.loads(resp.raw.decode("utf-8"))
            msg = data['error'] if data is not None and 'error' in data else 'No error data send'
        elif resp.data is not None and 'error' in resp.data:
            msg = resp.data['error']
        else:
            msg = f'Unknown Monolith error {resp.data}'

        logger.debug('ESI responded with status Monolith 520 and msg %s', msg)
    else:
        msg = resp.data['error'] if resp.data is not None and 'error' in resp.data else 'No error data send'
        logger.error('ESI responded with status %s and msg %s', resp.status, msg)

    return msg


def make_error_response(resp: Any) -> ESIResponse:
    msg: str = get_error_msg_from_response(resp)
    return ESIResponse(get_expire_time(resp), resp.status, msg)


def get_esi_client(token: Optional[SSOToken], noauth: bool = False) -> EsiClient:
    return get_esi_client_for_account(token, noauth)


def get_esi_client_for_account(token: Optional[SSOToken], noauth: bool = False) -> EsiClient:
    if noauth:
        return EsiClient(timeout=20, headers={'User-Agent': config.user_agent}, cache=DummyCache())

    signal: Signal = Signal()
    signal.add_receiver(SSOToken.update_token_callback)

    security = EsiSecurity(
        crest_return_url,
        crest_client_id,
        crest_client_secret,
        headers={'User-Agent': config.user_agent},
        signal_token_updated=signal,
        token_identifier=token.tokenID
    )
    security.update_token(token.info_for_esi_security())
    return EsiClient(security, timeout=20, headers={'User-Agent': config.user_agent}, cache=DummyCache())
