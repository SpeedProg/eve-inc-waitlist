from typing import List, Dict
from waitlist.utility.outgate.exceptions import check_esi_response
import logging
from waitlist.utility.swagger.eve.universe import UniverseEndpoint
from waitlist.utility.utils import chunks
from waitlist.utility.swagger.eve.universe.models import NameItem
from waitlist.utility.swagger.eve.universe.responses import ResolveIdsResponse

logger = logging.getLogger(__name__)


def get_names_for_ids(id_list: List[int], *args) -> Dict[int, NameItem]:
    """
    Get item info for a list of ids
    :throws ApiException when something went wrong with the api
    """
    # we should split in chunks of 1000
    ep = UniverseEndpoint()
    data: Dict[int, NameItem] = dict()
    for c in chunks(id_list, 1000):
        d = __get_names_for_ids(ep, c, args)
        data.update(d)

    return data


def __get_names_for_ids(ep: UniverseEndpoint, id_list: List[int], count=1,
                        *args):
    resp: ResolveIdsResponse = ep.resolve_ids(id_list)

    if resp.is_error():
        if count <= 5:
            return __get_names_for_ids(id_list, count+1, args)
        # this will just throw an ApiException
        return check_esi_response(resp,
                                  get_names_for_ids, args)

    data = dict()
    for item in resp.data:
        data[item.id] = item
    return data
