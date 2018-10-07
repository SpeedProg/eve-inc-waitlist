import logging
from typing import Union

from esipy import EsiClient
from urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger.eve.corporation.responses import CorporationInfo
from waitlist.utility.swagger.eve import get_esi_client, get_expire_time,\
    make_error_response, ESIEndpoint, ESIResponse

logger = logging.getLogger(__name__)


class CorporationEndpoint(ESIEndpoint):
    def __init__(self) -> None:
        super().__init__()
        self.esi_client: EsiClient = get_esi_client(None, True,
                                                    retry_request=True)

    def get_corporation_info(self, corp_id: int) -> Union[
            CorporationInfo,
            ESIResponse]:

        try:
            resp = self.\
                esi_client.request(self._api()
                                   .op['get_corporations_corporation_id'](
                                       corporation_id=corp_id))
            if resp.status == 200:
                return CorporationInfo(get_expire_time(resp), resp.status,
                                       None, resp.data)
            else:
                logger.error(f'Failed to get corp info for id={corp_id}')
                return make_error_response(resp)

        except ReadTimeoutError as e:
            logger.error(f'ESI Read Timeout on get_corporation_info {e}')
            raise e
