import logging

from requests.packages.urllib3.exceptions import ReadTimeoutError

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import get_esi_client, get_expire_time
from waitlist.utility.swagger.eve.character.responses import CharacterInfo

logger = logging.getLogger(__name__)


def get_character_info(char_id: int) -> CharacterInfo:
    api_v4 = get_api('v4')
    client_v4 = get_esi_client('v4', True)
    try:
        resp = client_v4.request(api_v4.op['get_characters_character_id'](character_id=char_id))
        if resp.status == 200:
            return CharacterInfo(get_expire_time(resp), resp.status, None, resp.data)
        else:
            msg = resp.data['error'] if 'error' in resp.data else 'No error data send'
            logger.error(f'ESI responded with status {resp.status} and msg {msg}')

    except ReadTimeoutError as e:
        logger.error(f'ESI Read Timeout on get_characters_character_id')
