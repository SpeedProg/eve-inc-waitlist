from esipy.client import EsiClient
from waitlist.utility.swagger.eve import get_esi_client
from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve.universe.responses import ResolveIdsResponse


class UniverseEndpoint(object):
    def __init__(self, client: EsiClient = None) -> None:
        if client is None:
            self.__client: EsiClient = get_esi_client(None, False)
            self.__api: App = get_api()
        else:
            self.__client: EsiClient = client
            self.__api: App = get_api()

    def resolve_ids(self, ids_list: [int]) -> ResolveIdsResponse:
        """
        :param list maximum of 1000 ids allowed at once
        """
        resp = self.__client.request(
            self.__api.op['post_universe_names'](ids=ids_list))

        return ResolveIdsResponse(resp)
