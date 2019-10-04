import logging
from datetime import datetime
from typing import Optional, Tuple

from waitlist.storage.database import APICacheCharacterInfo, SSOToken
from waitlist.utility.outgate.exceptions import check_esi_response, ESIException,\
    ApiException
from waitlist.utility.swagger.eve.character import CharacterEndpoint, CharacterInfo
from waitlist.utility.swagger.eve.search import SearchEndpoint, SearchResponse
from waitlist.base import db

logger = logging.getLogger(__name__)


def __run_update_check(self: APICacheCharacterInfo, char_id: int, *args):
    """
    :throws ApiException if an error with the api occured
    """
    if self.expire is None or self.expire < datetime.now():
        char_ep = CharacterEndpoint()
        info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), __run_update_check, args)
        self.id = char_id
        self.allianceID = info.get_alliance_id()
        self.characterName = info.get_name()
        self.corporationID = info.get_corp_id()
        self.characterBirthday = info.get_birthday()
        self.raceID = info.get_race_id()
        self.expire = info.expires()
        db.session.commit()


def get_character_info(char_id: int, *args) -> APICacheCharacterInfo:
    """
    Get Info for a character by id
    :param char_id: character id to get the info for
    :return: APICacheCharacterInfo of the character
    :throws ApiException if a problem with the api occured
    """
    char_cache = db.session.query(APICacheCharacterInfo).get(char_id)

    if char_cache is None:
        char_cache = APICacheCharacterInfo()
        db.session.add(char_cache)

    __run_update_check(char_cache, char_id)

    return char_cache


def get_character_info_by_name(name: str, *args) -> Optional[APICacheCharacterInfo]:
    """
    Get Info for a character by name
    :param name: character name to get the info for
    :return: APICacheCharacterInfo of the character or None if no character with this name can be found
    :throws ApiException if a problem with the api occured
    """
    char_cache = db.session.query(APICacheCharacterInfo)\
        .filter(APICacheCharacterInfo.characterName == name).first()

    if char_cache is not None:
        __run_update_check(char_cache, char_cache.id)

        # lets make sure with updated info the names still match
        if char_cache.characterName.lower() == name.lower():
            return char_cache

    search_ep = SearchEndpoint()
    search_info: SearchResponse = check_esi_response(search_ep.public_search(name, ['character']),
                                                        get_character_info_by_name, args)
    if search_info.character_ids() is None or\
        len(search_info.character_ids()) < 1:
        return None
    return get_character_info(search_info.character_ids()[0])


def get_char_or_corp_or_alliance_id_by_name(name: str, *args) -> Tuple[Optional[int], Optional[str]]:
    """
    Tuple of id and "character", "corporation", "alliance"
    or None, None
    :throws ApiException if something goes wrong on the api
    """
    search_ep = SearchEndpoint()
    search_results: SearchResponse = check_esi_response(
        search_ep.public_search(name, ['character', 'corporation', 'alliance']),
        get_char_or_corp_or_alliance_id_by_name, args)

    ids = search_results.ids(['character'])
    if len(ids) > 0:
        return ids[0],  'character'
    ids = search_results.ids(['corporation'])
    if len(ids) > 0:
        return ids[0], 'corporation'
    ids = search_results.ids(['alliance'])
    if len(ids) > 0:
        return ids[0], 'alliance'
    return None, None


def get_character_fleet_id(token: SSOToken, char_id: int) -> Optional[int]:
    """
    Get the fleet id for a character, or None if it is in no fleet
    :param token: the SSOToken of the fleetboss
    :param char_id:  character that should be in a fleet
    :return: fleet id or None if in no fleet
    """
    char_ep = CharacterEndpoint()
    resp = char_ep.get_fleet_info(token, char_id)
    if resp.is_error():
        logger.error(f"Failed to get fleet id."
                     f" Error Code is: {resp.get_monolith_error() if resp.is_monolith_error() else resp.error()}")
        return None
    return resp.get_fleet_id()
