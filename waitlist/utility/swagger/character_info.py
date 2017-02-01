"""
@return corp_id, alliance_id
"""
from waitlist.utility.swagger import api
import email.utils as eut
from email._parseaddr import mktime_tz
from pyswagger import Security
from pyswagger.contrib.client.requests import Client
import datetime
from waitlist.utility.swagger.eve import get_esi_client, ESIResponse,\
    get_expire_time
from typing import Dict, Any, Tuple
from esipy.client import EsiClient
# object = {'id':char_id, 'name': char_name, 'allianceID': alliance_id, 'allianceName': alliance_name, 'corporationID': corp_id, 'corporationName': corp_name, 'expire': expire}
def get_affiliation_info(char_id: int) -> Dict[str, Any]:
    security = Security(
        api,
    )
    client = Client(security)
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
    char_answer = client.request(api.op['get_characters_character_id'](character_id=char_id))
    char_name = char_answer.data['name']
    corp_id = int(char_answer.data['corporation_id'])
    char_answer_expire = mktime_tz(eut.parsedate_tz(char_answer.header['Expires'][0]))

    corp_answer = client.request(api.op['get_corporations_corporation_id'](corporation_id=corp_id))
    corp_answer_expire = mktime_tz(eut.parsedate_tz(corp_answer.header['Expires'][0]))
    corp_name = corp_answer.data['corporation_name']
    alliance_id = 0
    alliance_name = ''
    expires = max(char_answer_expire, corp_answer_expire)
    if ('alliance_id' in corp_answer.data):
        alliance_id = int(corp_answer.data['alliance_id'])
        all_answer = client.request(api.op['get_alliances_alliance_id'](alliance_id=alliance_id))
        alliance_name = all_answer.data['alliance_name']
        all_answer_expire = mktime_tz(eut.parsedate_tz(all_answer.header['Expires'][0]))
        expires = max(expires, all_answer_expire)

    return  {'id':char_id, 'name': char_name, 'allianceID': alliance_id, 'allianceName': alliance_name, 'corporationID': corp_id, 'corporationName': corp_name, 'expire': expires}
'''
@return charid, name
'''
def characterid_from_name(charName: str) -> Tuple[int, str]:
    security = Security(
        api,
    )
    client = Client(security)
    search_answer = client.request(api.op['get_search'](search=charName, categories=['character'], strict=True))
    # this character name doesn't exist
    if (not ('character' in search_answer.data)):
        return None, None
    char_id: int = int(search_answer.data['character'][0])
    
    char_answer = client.request(api.op['get_characters_character_id'](character_id=char_id))
    char_name: str = char_answer.data['name']
    
    return char_id, char_name

def get_character_info(char_id: int) -> Tuple[Dict[str, Any], datetime.datetime]:
    security = Security(
        api,
    )
    client = Client(security)
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
    char_answer = client.request(api.op['get_characters_character_id'](character_id=char_id))
    corp_id = int(char_answer.data['corporation_id'])
    char_answer_expire = mktime_tz(eut.parsedate_tz(char_answer.header['Expires'][0]))

    corp_answer = client.request(api.op['get_corporations_corporation_id'](corporation_id=corp_id))
    corp_answer_expire = mktime_tz(eut.parsedate_tz(corp_answer.header['Expires'][0]))
    expires = max(char_answer_expire, corp_answer_expire)
    ret = char_answer.data.update(corp_answer.data)
    return ret, datetime.datetime.fromtimestamp(expires)


def open_information(target_id: int) -> ESIResponse:
    client: EsiClient = get_esi_client()

    resp = client.request(api.op['post_ui_openwindow_information'](target_id=target_id))
    if resp.status == 204:
        return ESIResponse(get_expire_time(resp), resp.status, None)
    return ESIResponse(get_expire_time(resp), resp.status,
                       resp.data['error'])
