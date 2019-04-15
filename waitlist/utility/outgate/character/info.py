import logging
from datetime import datetime
from typing import Optional, Tuple

from waitlist.storage.database import APICacheCharacterInfo, APICacheCorporationInfo, SSOToken
from waitlist.utility.outgate.exceptions import check_esi_response, ESIException,\
    ApiException
from waitlist.utility.swagger.eve.character import CharacterEndpoint, CharacterInfo
from waitlist.utility.swagger.eve.search import SearchEndpoint, SearchResponse
from waitlist.base import db
from waitlist.utility.outgate import corporation

logger = logging.getLogger(__name__)


def set_from_character_info(self: APICacheCharacterInfo, info: CharacterInfo, char_id: int) -> None:
    self.id = char_id
    self.characterName = info.get_name()
    self.corporationID = info.get_corp_id()
    self.characterBirthday = info.get_birthday()
    self.raceID = info.get_race_id()
    self.expire = info.expires()


def get_character_info(char_id: int, *args) -> APICacheCharacterInfo:
    """
    :throws ApiException if an error with the api occured
    """
    char_cache: APICacheCharacterInfo = db.session.query(APICacheCharacterInfo) \
        .filter(APICacheCharacterInfo.id == char_id).first()

    if char_cache is None:
        char_cache = APICacheCharacterInfo()
        char_ep = CharacterEndpoint()
        char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
        char_cache.id = char_id
        set_from_character_info(char_cache, char_info, char_id)
        db.session.add(char_cache)
        db.session.commit()
    elif char_cache.characterName is None:
        char_ep = CharacterEndpoint()
        char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
        set_from_character_info(char_cache, char_info, char_id)
        db.session.commit()
    else:
        now = datetime.now()
        if char_cache.expire is None or char_cache.expire < now:
            # expired, update it
            char_ep = CharacterEndpoint()
            char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
            set_from_character_info(char_cache, char_info, char_id)
            db.session.commit()

    return char_cache


def get_character_info_by_name(name: str, *args) -> Optional[APICacheCharacterInfo]:
    """
    Get Info for a character by name
    :param name: character name to get the info for
    :return: APICacheCharacterInfo of the character or None if no character with this name can be found
    :throws ApiException if a problem with the api occured
    """
    character = db.session.query(APICacheCharacterInfo).filter(APICacheCharacterInfo.characterName == name).first()
    if character is None:
        search_ep = SearchEndpoint()
        search_info: SearchResponse = check_esi_response(search_ep.public_search(name, ['character']),
                                                         get_character_info_by_name, args)
        if search_info.character_ids() is None or\
           len(search_info.character_ids()) < 1:
            return None
        return get_character_info(search_info.character_ids()[0])
    else:
        # this does expire checks and such for us
        info: APICacheCharacterInfo = get_character_info(character.id)
        # lets make sure with updated info the names still match
        if info.characterName.lower() != name.lower():
            # if they don't, try to find a char for it
            search_ep = SearchEndpoint()
            search_info: SearchResponse = check_esi_response(search_ep.public_search(name, ['character']),
                                                             get_character_info_by_name, args)

            return get_character_info(search_info.character_ids()[0])

        return info


def get_char_or_corp_or_alliance_id_by_name(name: str, *args) -> Optional[int]:
    """
    :throws ApiException if something goes wrong on the api
    """
    search_ep = SearchEndpoint()
    search_results: SearchResponse = check_esi_response(
        search_ep.public_search(name, ['character', 'corporation', 'alliance']),
        get_char_or_corp_or_alliance_id_by_name, args)
    ids = search_results.ids(['character', 'corporation', 'alliance'])
    if len(ids) < 1:
        return None
    return ids[0]


def get_char_affiliations(char_id: int, *_) -> Optional[Tuple[int, int]]:
    """
    Get the id of a characters corporation and alliance
    :param char_id: characters id
    :return a Tuple[CorpID, AllianceID], alliance could ne None
    :throws ApiException if there was a problem with the api
    """
    char_info: APICacheCharacterInfo = get_character_info(char_id)
    corp_info: APICacheCorporationInfo = corporation.get_info(char_info.corporationID)
    return corp_info.id, corp_info.allianceID


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
