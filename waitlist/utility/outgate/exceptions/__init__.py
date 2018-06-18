import logging
from typing import Callable, Any, Optional, Sequence

from waitlist.utility.swagger.eve import ESIResponse

logger = logging.getLogger(__name__)


class ApiException(Exception):
    """Base class for Api Exceptions"""
    pass


class ESIException(ApiException):
    """
    Base class for sending esi based api exceptions
    """

    def __init__(self, error_response: Optional[ESIResponse], call: Callable) -> None:
        self.__resp = error_response
        self.__call = call

    def get_response(self) -> Optional[ESIResponse]:
        return self.__resp

    def get_call(self) -> Callable:
        return self.__call

    def __repr__(self):
        return f'<ESIException caller={self.get_call().__name__} resp={self.get_response()}>'


def check_esi_response(resp: Optional[ESIResponse], call: Callable, params: Sequence[Any]) -> ESIResponse:
    if resp is None:
        # this should never happen
        logger.error('Got no response in {} with {}', call.__name__, params)
        raise ESIException(resp, call)
    elif resp.is_error():
        # esi returned no data
        logger.info('Got ESIResponse {}', resp)
        raise ESIException(resp, call)
    else:
        return resp
