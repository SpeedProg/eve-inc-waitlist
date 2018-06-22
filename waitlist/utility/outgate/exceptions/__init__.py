import logging
from typing import Callable, Any, Optional, Sequence, Dict

from waitlist.utility.swagger.eve import ESIResponse
from flask import jsonify

logger = logging.getLogger(__name__)


class ApiException(Exception):
    """
    This exception is thrown to the outside world.
    """
    def __init__(self, error_msg: str, http_code: int):
        self.msg = error_msg
        self.code = http_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            'msg': self.error_msg,
            'code': self.http_code,
            }

    def __str__(self):
        return jsonify(self.to_dict());

    def __repr__(self):
        return f'<GernericApiException code={self.code} msg={self.msg}>'


class ESIException(ApiException):
    """
    Base class for sending esi based api exceptions
    """

    def __init__(self, error_response: Optional[ESIResponse], call: Callable) -> None:
        if error_response is None or not error_response.is_error():
            super(ESIException, self).__init__('No Response provided', 500)
        else:
            super(ESIException, self).__init__(error_response.error(), error_response.code())
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
