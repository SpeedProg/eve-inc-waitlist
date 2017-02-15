"""
@return corp_id, alliance_id
"""
from pyswagger import App

from waitlist.utility.swagger import get_api
import email.utils as eut
from pyswagger import Security
import datetime
from waitlist.utility.swagger.eve import get_esi_client, ESIResponse,\
    get_expire_time
from typing import Dict, Any, Tuple, Optional
from waitlist.utility.swagger.patch import EsiClient, PatchClient as Client


def get_affiliation_info(char_id: int) -> Dict[str, Any]:

    api_v4 = get_api('v4')
    client_v4 = get_esi_client('v4', True)

    api_v2 = get_api('v2')
    client_v2 = get_esi_client('v2', True)

    '''
{
"corporation_id": 98143274,
"birthday": "2011-12-17T14:58:54Z",
"name": "Bruce Warhead",
"gender": "male",
"race_id": 1,
"description": "<br>Beryl Slanjava &gt; had all eve windows open and was faster to reboot than close them",
"bloodline_id": 1,
"ancestry_id": 11,
"security_status": 5.000946212150391
}
    '''
    char_answer = client_v4.request(api_v4.op['get_characters_character_id'](character_id=char_id))
    char_name = char_answer.data['name']
    corp_id = int(char_answer.data['corporation_id'])
    char_answer_expire = get_expire_time(char_answer)

    corp_answer = client_v2.request(api_v2.op['get_corporations_corporation_id'](corporation_id=corp_id))
    corp_answer_expire = get_expire_time(corp_answer)
    corp_name = corp_answer.data['corporation_name']
    alliance_id = 0
    alliance_name = ''
    expires = max(char_answer_expire, corp_answer_expire)
    if 'alliance_id' in corp_answer.data:
        alliance_id = int(corp_answer.data['alliance_id'])
        all_answer = client_v2.request(api_v2.op['get_alliances_alliance_id'](alliance_id=alliance_id))
        alliance_name = all_answer.data['alliance_name']
        all_answer_expire = get_expire_time(all_answer)
        expires = max(expires, all_answer_expire)

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


def get_character_info(char_id: int) -> Tuple[Dict[str, Any], datetime.datetime]:
    api_v4 = get_api('v4')
    security = Security(
        api_v4,
    )
    client_v4 = Client(security, timeout=10)

    api_v2 = get_api('v2')
    security_v2 = Security(
        api_v2,
    )
    client_v2 = Client(security_v2, timeout=10)
    '''
{
"corporation_id": 98143274,
"birthday": "2011-12-17T14:58:54Z",
"name": "Bruce Warhead",
"gender": "male",
"race_id": 1,
"description": "<br>Beryl Slanjava &gt; had all eve windows open and was faster to reboot than close them",
"bloodline_id": 1,
"ancestry_id": 11,
"security_status": 5.000946212150391
}merged with
   {
    "alliance_id": 434243723,
    "ceo_id": 180548812,
    "corporation_name": "C C P",
    "member_count": 656,
    "ticker": "-CCP-"
  }
, expire_datetime
    '''
    char_answer = client_v4.request(api_v4.op['get_characters_character_id'](character_id=char_id))
    corp_id = int(char_answer.data['corporation_id'])
    char_answer_expire = get_expire_time(char_answer)

    corp_answer = client_v2.request(api_v2.op['get_corporations_corporation_id'](corporation_id=corp_id))
    corp_answer_expire = get_expire_time(corp_answer)
    expires = max(char_answer_expire, corp_answer_expire)
    ret = char_answer.data.update(corp_answer.data)
    return ret, datetime.datetime.fromtimestamp(expires)


def open_information(target_id: int) -> ESIResponse:
    api_v1: App = get_api('v1')
    client: EsiClient = get_esi_client('v1')

    resp = client.request(api_v1.op['post_ui_openwindow_information'](target_id=target_id))
    if resp.status == 204:
        return ESIResponse(get_expire_time(resp), resp.status, None)
    return ESIResponse(get_expire_time(resp), resp.status,
                       resp.data['error'])
