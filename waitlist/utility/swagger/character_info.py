"""
@return corp_id, alliance_id
"""
from pyswagger import App

from utility.swagger.eve.alliance import AllianceEndpoint
from utility.swagger.eve.character import CharacterEndpoint, CharacterInfo
from utility.swagger.eve.corporation import CorporationEndpoint
from waitlist.utility.swagger import get_api
from pyswagger import Security
import datetime

from waitlist.utility.swagger.eve import get_esi_client, ESIResponse,\
    get_expire_time
from typing import Dict, Any, Tuple, Optional
from waitlist.utility.swagger.patch import EsiClient, PatchClient as Client


def get_affiliation_info(char_id: int) -> Dict[str, Any]:
    c_ep = CharacterEndpoint()
    char_data: CharacterInfo = c_ep.get_character_info(char_id)
    char_name = char_data.get_name()
    corp_id = char_data.get_corp_id()
    char_answer_expire = char_data.expires()

    corp_ep = CorporationEndpoint()

    corp_answer = corp_ep.get_corporation_info(corp_id)
    corp_answer_expire: datetime = corp_answer.expires()
    corp_name = corp_answer.get_corporation_name()
    alliance_id = 0
    alliance_name = ''
    expires = char_answer_expire if char_answer_expire > corp_answer_expire else corp_answer_expire
    if corp_answer.get_alliance_id() is not None:
        alliance_id = corp_answer.get_alliance_id()
        all_ep = AllianceEndpoint()
        all_answer = all_ep.get_alliance_info(alliance_id)
        alliance_name = all_answer.get_alliance_name()
        all_answer_expire = all_answer.expires()
        expires = expires if expires > all_answer_expire else all_answer_expire

    return {'id': char_id, 'name': char_name, 'allianceID': alliance_id, 'allianceName': alliance_name,
            'corporationID': corp_id, 'corporationName': corp_name, 'expire': expires}


def characterid_from_name(char_name: str) -> Tuple[Optional[int], Optional[str]]:
    """
    @return charid, name
    """
    api_v4 = get_api('v4')
    security_v4 = Security(
        api_v4,
    )
    client_v4 = Client(security_v4, timeout=10)

    api_v1 = get_api('v1')
    security_v1 = Security(
        api_v1,
    )
    client_v1 = Client(security_v1, timeout=10)

    search_answer = client_v1.request(api_v1.op['get_search'](search=char_name, categories=['character'], strict=True))

    # this character name doesn't exist
    if not ('character' in search_answer.data):
        return None, None
    char_id: int = int(search_answer.data['character'][0])
    
    char_answer = client_v4.request(api_v4.op['get_characters_character_id'](character_id=char_id))
    char_name: str = char_answer.data['name']
    
    return char_id, char_name


def open_information(target_id: int) -> ESIResponse:
    api_v1: App = get_api('v1')
    client: EsiClient = get_esi_client('v1')

    resp = client.request(api_v1.op['post_ui_openwindow_information'](target_id=target_id))
    if resp.status == 204:
        return ESIResponse(get_expire_time(resp), resp.status, None)
    return ESIResponse(get_expire_time(resp), resp.status,
                       resp.data['error'])
