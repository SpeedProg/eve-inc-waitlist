import logging
from esipy import EsiClient

from requests.packages.urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger.eve import get_esi_client, get_expire_time, make_error_response, ESIEndpoint
from waitlist.utility.swagger.eve.character.responses import CharacterInfo

logger = logging.getLogger(__name__)


class CharacterEndpoint(ESIEndpoint):
    def __init__(self) -> None:
        self._add_esi_api('v4')
        self.esi_client: EsiClient = get_esi_client('v4', True)  # version doesn't matter if we use no auth
        pass

    def get_character_info(self, char_id: int) -> CharacterInfo:
        # check the endpoints we need are in there
        if not (ESIEndpoint.is_endpoint_available(self._api('v4'), 'get_characters_character_id')):
            self._add_esi_api('v4')

        try:
            resp = self.esi_client.request(self._api('v4').op['get_characters_character_id'](character_id=char_id))
            if resp.status == 200:
                return CharacterInfo(get_expire_time(resp), resp.status, None, resp.data)
            else:
                return make_error_response(resp)

        except ReadTimeoutError as e:
            logger.error(f'ESI Read Timeout on get_characters_character_id {e}')
            raise e
