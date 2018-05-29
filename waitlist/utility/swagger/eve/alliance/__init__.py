import logging
from typing import Union

from esipy import EsiClient
from urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger.eve.alliance.responses import AllianceInfo
from waitlist.utility.swagger.eve import get_esi_client, get_expire_time, make_error_response, ESIEndpoint, ESIResponse

logger = logging.getLogger(__name__)


class AllianceEndpoint(ESIEndpoint):
    def __init__(self) -> None:
        super().__init__()
        self.esi_client: EsiClient = get_esi_client(None, True)

    def get_alliance_info(self, all_id: int) -> Union[AllianceInfo, ESIResponse]:

        try:
            resp = self.esi_client.request(self._api().op['get_alliances_alliance_id'](alliance_id=all_id))
            if resp.status == 200:
                return AllianceInfo(get_expire_time(resp), resp.status, None, resp.data)
            else:
                logger.error(f'Failed to get alliance info for id={all_id}')
                return make_error_response(resp)

        except ReadTimeoutError as e:
            logger.error(f'ESI Read Timeout on get_alliance_info {e}')
            raise e
