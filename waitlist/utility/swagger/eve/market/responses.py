from typing import Any, ClassVar, List
from .. import ESIResponse, get_expire_time, get_error_msg_from_response


class MarketGroupsResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in MarketGroupsResponse.okay_codes:
            super(MarketGroupsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__ids = response.data
        else:
            error_msg = get_error_msg_from_response(response)
            super(MarketGroupsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    @property
    def data(self) -> List[int]:
        """
        Get the list of marketgroup ids
        :returns list of marketgroup ids
        """
        return self.__ids


class MarketGroupResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in MarketGroupResponse.okay_codes:
            super(MarketGroupResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.id = response.data['market_group_id']
            self.parent_id = response.data['parent_group_id'] if 'parent_group_id' in response.data else None
            self.name = response.data['name']
            self.description = response.data['description']
            # this is a list of ids
            self.types = response.data['types']
        else:
            error_msg = get_error_msg_from_response(response)
            super(MarketGroupResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)
    def __repr__(self):
        return f'<MarketGroupResponse code={self.code()} error={self.error()} expires={self.expires()} id={self.id} parent_id={self.parent_id} name={self.name}>'

