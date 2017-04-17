import logging
from esipy import EsiClient

from requests.packages.urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger.eve.corporation.responses import CorporationInfo
from waitlist.utility.swagger.eve import get_esi_client, get_expire_time, make_error_response, ESIEndpoint

logger = logging.getLogger(__name__)


class CorporationEndpoint(ESIEndpoint):
    def __init__(self) -> None:
        self._add_esi_api('v3')
        self.esi_client: EsiClient = get_esi_client('', True)  # version doesn't matter if we use no auth
        pass

    def get_corporation_info(self, corp_id: int) -> CorporationInfo:
        # check the endpoints we need are in there
        if not (ESIEndpoint.is_endpoint_available(self._api('v3'), 'get_corporations_corporation_id')):
            self._try_reload_api('v3')

        try:
            resp = self.esi_client.request(self._api('v3')
                                           .op['get_corporations_corporation_id'](corporation_id=corp_id))
            if resp.status == 200:
                return CorporationInfo(get_expire_time(resp), resp.status, None, resp.data)
            else:
                msg = resp.data['error'] if 'error' in resp.data else 'No error data send'
                logger.error(f'get_corporation_info ESI responded with status {resp.status} and msg {msg}')
                return make_error_response(resp)

        except ReadTimeoutError as e:
            logger.error(f'ESI Read Timeout on get_corporation_info {e}')
            raise e
