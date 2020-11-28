from esipy.client import EsiClient
from typing import List
from ...eve import get_esi_client
from ....swagger import get_api
from .responses import MarketGroupsResponse, MarketGroupResponse
from pyswagger.core import App


class MarketEndpoint(object):
    def __init__(self, client: EsiClient = None) -> None:
        if client is None:
            self.__client: EsiClient = get_esi_client(
                token=None, noauth=True, retry_request=True)
            self.__api: App = get_api()
        else:
            self.__client: EsiClient = client
            self.__api: App = get_api()

    def get_groups(self) -> MarketGroupsResponse:
        """
        Get response containing a list of all group ids
        """
        resp = self.__client.request(
            self.__api.op['get_markets_groups']())
        return MarketGroupsResponse(resp)

    def get_group(self, group_id: int) -> MarketGroupResponse:
        """
        Get response containing information about the group
        """
        resp = self.__client.request(
            self.__api.op['get_markets_groups_market_group_id'](
                market_group_id=group_id))
        return MarketGroupResponse(resp)

    def get_group_multi(self,
                           group_ids: List[int]) -> List[MarketGroupResponse]:
        ops = []
        for group_id in group_ids:
            ops.append(self.__api.op['get_markets_groups_market_group_id'](
                market_group_id=group_id))

        response_infos = self.__client.multi_request(ops)
        return [MarketGroupResponse(info[1]) for info in response_infos]

