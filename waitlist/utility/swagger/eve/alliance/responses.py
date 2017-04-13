import logging
from datetime import datetime
from typing import Optional, Union, Dict

from waitlist.utility.swagger.eve import ESIResponse

logger = logging.getLogger(__name__)


class AllianceInfo(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 data: Optional[Dict[str, Union[str, int, float]]]) -> None:
        super(AllianceInfo).__init__(expires, status_code, error)
        self.data: Optional[Dict[str, Union[str, int, datetime]]] = data
        if self.data is not None and 'date_founded' in self.data:
            self.data['date_founded'] = ESIResponse.parse_datetime(self.data['date_founded'])

    def get_alliance_name(self) -> str:
        return self.data['alliance_name']

    def get_date_founded(self) -> datetime:
        return self.data['date_founded']

    def get_executor_corp_id(self) -> int:
        return self.data['executor_corp']

    def get_ticker(self) -> str:
        return self.data['ticker']
