import logging
from datetime import datetime
from typing import Optional, Dict, Sequence, List

from waitlist.utility.swagger.eve import ESIResponse

logger = logging.getLogger(__name__)


class SearchResponse(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 data: Optional[Dict[str, Sequence[int]]]) -> None:
        super(SearchResponse).__init__(expires, status_code, error)
        self.data: Optional[Dict[str, Sequence[int]]] = data

    def character_ids(self) -> Optional[Sequence[int]]:
        return self.__get_ids('character')

    def ids(self, types: Sequence[str]):
        result: List[int] = []
        for type_name in types:
            r = self.__get_ids(type_name)
            if r is not None:
                result.extend(r)
        return result

    def __get_ids(self, name: str) -> Optional[Sequence[int]]:
        if name not in self.data:
            return None
        return self.data[name]

