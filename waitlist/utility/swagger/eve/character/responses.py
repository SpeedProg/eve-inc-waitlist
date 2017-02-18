import logging
from datetime import datetime
from typing import Optional, Set, Union

from waitlist.utility.swagger.eve import ESIResponse

logger = logging.getLogger(__name__)


class CharacterInfo(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str], data: Optional[Set[str, Union[str, int]]]) -> None:
        super(CharacterInfo).__init__(expires, status_code, error)
        self.data = data

    def get_birthday(self) -> datetime:
        return self.data['birthday']

    def get_corp_id(self) -> int:
        return self.data['corporation_id']

    def get_name(self) -> str:
        return self.data['name']

    def get_race_id(self) -> int:
        return self.data['race_id']

