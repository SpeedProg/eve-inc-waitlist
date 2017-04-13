import logging
from datetime import datetime
from pyswagger.primitives import Datetime
from typing import Optional, Union, Dict

from waitlist.utility.swagger.eve import ESIResponse

logger = logging.getLogger(__name__)


class AllianceInfo(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 data: Optional[Dict[str, Union[str, int, float, Datetime]]]) -> None:
        super().__init__(expires, status_code, error)
        self.data: Optional[Dict[str, Union[str, int, float, Datetime]]] = data

    def get_alliance_name(self) -> str:
        return self.data['alliance_name']

    def get_date_founded(self) -> datetime:
        return self.data['date_founded'].v

    def get_executor_corp_id(self) -> int:
        return self.data['executor_corp']

    def get_ticker(self) -> str:
        return self.data['ticker']
