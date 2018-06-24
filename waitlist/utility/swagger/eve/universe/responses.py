from waitlist.utility.swagger.eve import ESIResponse, get_expire_time,\
    get_error_msg_from_response
import datetime
from typing import Optional, Any, ClassVar, List, Dict
from waitlist.utility.swagger.eve.universe.models import NameItem


class ResolveIdsResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in ResolveIdsResponse.okay_codes:
            super(ResolveIdsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__data: Dict[int, NameItem] = set()
            self.__set_data(response.data)
        else:
            error_msg = get_error_msg_from_response(response)
            super(ResolveIdsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    def __set_data(self, data: List[Dict[str, Any]]):
        for item in data:
            self.__data[item.id] = NameItem(item)

    @property
    def data(self) -> Dict[int, NameItem]:
        """
        Get the requests data
        :returns dict of it to item info mapping,
         item info contains: id, name, category
        """
        return self.__data
