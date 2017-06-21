import logging
from esipy import EsiClient

from requests.packages.urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger.eve.alliance.responses import AllianceInfo
from waitlist.utility.swagger.eve import get_esi_client, get_expire_time, make_error_response, ESIEndpoint

logger = logging.getLogger(__name__)


class AllianceEndpoint(ESIEndpoint):
    def __init__(self) -> None:
        self._add_esi_api('v2')
        self.esi_client: EsiClient = get_esi_client('', True)  # version doesn't matter if we use no auth
        pass

    def get_alliance_info(self, all_id: int) -> AllianceInfo:
        # check the endpoints we need are in there
        if not (ESIEndpoint.is_endpoint_available(self._api('v2'), 'get_alliances_alliance_id')):
            self._try_reload_api('v2')

        try:
            resp = self.esi_client.request(self._api('v2').op['get_alliances_alliance_id'](alliance_id=all_id))
            if resp.status == 200:
                return AllianceInfo(get_expire_time(resp), resp.status, None, resp.data)
            else:
                logger.error(f'Failed to get alliance info for id={all_id}')
                return make_error_response(resp)

        except ReadTimeoutError as e:
            logger.error(f'ESI Read Timeout on get_alliance_info {e}')
            raise e
